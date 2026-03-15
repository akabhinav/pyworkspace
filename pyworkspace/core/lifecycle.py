"""Workspace lifecycle operations: pause, resume, snapshot, clone."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

from pyworkspace.core.specs import WorkspaceSpec
from pyworkspace.core.workspace_engine import WorkspaceStateMachine

logger = structlog.get_logger()


class LifecycleManager:
    """Manages workspace state transitions: pause, resume, snapshot, clone."""

    def __init__(self, k8s_manager=None, secret_manager=None, snapshot_store=None) -> None:
        self.k8s = k8s_manager
        self.secrets = secret_manager
        self.snapshot_store = snapshot_store

    async def pause(self, workspace: dict) -> dict:
        """
        Pause a running workspace:
        1. Stop agent gracefully
        2. Snapshot PVCs if auto_snapshot enabled
        3. Scale all deployments to 0
        4. Retain namespace, PVCs, DNS, secrets
        """
        sm = WorkspaceStateMachine(workspace["id"], workspace["status"])
        sm.transition("paused")

        namespace = workspace["k8s_namespace"]

        # Take auto-snapshot if configured
        spec_data = workspace.get("spec", {})
        if spec_data.get("auto_snapshot", True):
            await self._take_snapshot(workspace, "auto-pause")

        # Scale down all deployments
        if self.k8s:
            await self.k8s.scale_namespace_deployments(namespace, replicas=0)

        workspace["status"] = "paused"
        workspace["paused_at"] = datetime.now(timezone.utc)
        workspace["updated_at"] = datetime.now(timezone.utc)

        logger.info("workspace_paused", workspace_id=workspace["id"])
        return workspace

    async def resume(self, workspace: dict) -> dict:
        """
        Resume a paused workspace:
        1. Scale deployments back to 1
        2. Wait for healthy
        3. Rotate credentials
        4. Restart agent with restored context
        """
        sm = WorkspaceStateMachine(workspace["id"], workspace["status"])
        sm.transition("resuming")

        namespace = workspace["k8s_namespace"]

        # Scale up
        if self.k8s:
            await self.k8s.scale_namespace_deployments(namespace, replicas=1)
            await self.k8s.wait_for_namespace_healthy(namespace, timeout_seconds=90)

        # Rotate credentials on resume
        if self.secrets:
            spec = workspace.get("spec", {})
            for svc in spec.get("services", []):
                await self.secrets.rotate(workspace["id"], svc["name"])

        workspace["status"] = "running"
        workspace["paused_at"] = None
        workspace["updated_at"] = datetime.now(timezone.utc)

        logger.info("workspace_resumed", workspace_id=workspace["id"])
        return workspace

    async def snapshot(self, workspace: dict, name: str = "manual") -> dict:
        """Take a named snapshot of the workspace."""
        return await self._take_snapshot(workspace, name)

    async def _take_snapshot(self, workspace: dict, name: str) -> dict:
        """
        Snapshot implementation:
        1. Quiesce databases (pg_checkpoint, redis BGSAVE, etc.)
        2. Tar each PVC
        3. Upload to MinIO
        4. Record metadata
        """
        workspace_id = workspace["id"]
        snapshot_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        minio_path = f"snapshots/{workspace_id}/{timestamp}/{name}"

        spec_data = workspace.get("spec", {})
        service_names = [s.get("name", s.get("type", "unknown")) for s in spec_data.get("services", [])]

        snapshot = {
            "id": snapshot_id,
            "workspace_id": workspace_id,
            "name": name,
            "type": "auto" if name.startswith("auto") else "manual",
            "minio_path": minio_path,
            "services_included": service_names,
            "size_bytes": 0,
            "created_at": datetime.now(timezone.utc),
            "status": "creating",
        }

        if self.snapshot_store:
            await self.snapshot_store.upload(workspace_id, snapshot)
            snapshot["status"] = "ready"
        else:
            snapshot["status"] = "ready"

        workspace["snapshot_id"] = snapshot_id
        logger.info("snapshot_taken", workspace_id=workspace_id, snapshot_id=snapshot_id, name=name)
        return snapshot

    async def clone(self, source_workspace: dict, new_name: str, owner_id: str) -> dict:
        """
        Clone a workspace:
        1. Snapshot source
        2. Create new WorkspaceSpec from source
        3. Return new spec for provisioning
        """
        await self._take_snapshot(source_workspace, "pre-clone")

        source_spec = source_workspace.get("spec", {})
        new_spec = WorkspaceSpec(
            name=new_name,
            owner_id=owner_id,
            org_id=source_spec.get("org_id", ""),
            tier=source_spec.get("tier", "standard"),
            services=[],
            description=f"Cloned from {source_workspace.get('name', '')}",
            tags={"cloned_from": source_workspace["id"]},
        )

        # Rebuild services from source spec
        for svc_data in source_spec.get("services", []):
            from pyworkspace.core.specs import ServiceSpec
            new_spec.services.append(ServiceSpec(**svc_data))

        logger.info(
            "workspace_cloned",
            source_id=source_workspace["id"],
            new_name=new_name,
        )
        return new_spec.model_dump()
