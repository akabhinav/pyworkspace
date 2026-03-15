"""Clean workspace teardown and resource reclamation."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()


class WorkspaceDestroyer:
    """Destroys a workspace: stops agent, deletes K8s resources, wipes secrets, removes DNS."""

    def __init__(self, k8s_manager=None, secret_manager=None, dns_manager=None) -> None:
        self.k8s = k8s_manager
        self.secrets = secret_manager
        self.dns = dns_manager

    async def destroy(self, workspace: dict) -> dict:
        """
        Full teardown:
        1. Stop agent pod
        2. Delete all service pods/deployments
        3. Delete PVCs (crypto-erase)
        4. Remove Vault secrets
        5. Remove DNS entries
        6. Delete K8s namespace
        7. Mark workspace destroyed
        """
        workspace_id = workspace["id"]
        namespace = workspace.get("k8s_namespace")
        dns_zone = workspace.get("dns_zone")

        logger.info("workspace_destroy_started", workspace_id=workspace_id)

        # Delete namespace (cascades to all pods, services, PVCs)
        if self.k8s and namespace:
            await self.k8s.delete_namespace(namespace)

        # Wipe secrets from Vault
        if self.secrets:
            await self.secrets.delete_workspace_secrets(workspace_id)

        # Remove DNS zone
        if self.dns and dns_zone:
            await self.dns.remove_zone(dns_zone)

        workspace["status"] = "destroyed"
        workspace["updated_at"] = datetime.now(timezone.utc)

        logger.info("workspace_destroyed", workspace_id=workspace_id)
        return workspace
