"""Workspace CRD controller — orchestrates K8s resources for workspaces."""
from __future__ import annotations
import structlog

from pyworkspace.k8s.namespace_manager import NamespaceManager
from pyworkspace.k8s.pod_manager import PodManager
from pyworkspace.k8s.pvc_manager import PVCManager
from pyworkspace.k8s.rbac_manager import RBACManager

logger = structlog.get_logger()

class WorkspaceOperator:
    """
    High-level K8s operator that combines namespace, pod, PVC, and RBAC managers.
    Provides a unified interface for workspace K8s operations.
    """

    def __init__(self):
        self.namespace_mgr = NamespaceManager()
        self.pod_mgr = PodManager()
        self.pvc_mgr = PVCManager()
        self.rbac_mgr = RBACManager()

    async def initialize(self) -> None:
        await self.namespace_mgr.initialize()
        await self.pod_mgr.initialize()

    async def create_namespace(self, namespace: str, workspace_id: str) -> None:
        await self.namespace_mgr.create_namespace(namespace, workspace_id)

    async def delete_namespace(self, namespace: str) -> None:
        await self.namespace_mgr.delete_namespace(namespace)

    async def apply_manifest(self, manifest: dict) -> None:
        await self.pod_mgr.apply_manifest(manifest)

    async def apply_network_policy(self, namespace: str, workspace_id: str, egress_allowed: bool) -> None:
        await self.pod_mgr.apply_network_policy(namespace, workspace_id, egress_allowed)

    async def wait_for_healthy(self, namespace: str, service_name: str, timeout_seconds: int = 300) -> bool:
        return await self.pod_mgr.wait_for_healthy(namespace, service_name, timeout_seconds)

    async def wait_for_namespace_healthy(self, namespace: str, timeout_seconds: int = 90) -> bool:
        return await self.pod_mgr.wait_for_namespace_healthy(namespace, timeout_seconds)

    async def scale_namespace_deployments(self, namespace: str, replicas: int) -> None:
        await self.pod_mgr.scale_namespace_deployments(namespace, replicas)

    async def get_namespace_resource_metrics(self, namespace: str) -> dict:
        return await self.pod_mgr.get_namespace_resource_metrics(namespace)

    async def setup_rbac(self, namespace: str, workspace_id: str) -> list[dict]:
        manifests = [
            self.rbac_mgr.build_service_account(namespace, workspace_id),
            self.rbac_mgr.build_role(namespace, workspace_id),
            self.rbac_mgr.build_role_binding(namespace, workspace_id),
        ]
        for m in manifests:
            await self.apply_manifest(m)
        return manifests
