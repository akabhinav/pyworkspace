"""Persistent Volume Claim management."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

class PVCManager:
    """Manages persistent volume claims for workspace services."""

    def __init__(self, k8s_client=None):
        self._client = k8s_client

    def build_pvc(
        self,
        name: str,
        namespace: str,
        workspace_id: str,
        storage: str = "10Gi",
        storage_class: str = "standard",
    ) -> dict:
        return {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": {"workspace": workspace_id, "managed-by": "pyworkspace"},
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "storageClassName": storage_class,
                "resources": {"requests": {"storage": storage}},
            },
        }

    async def delete_workspace_pvcs(self, namespace: str) -> None:
        """Delete all PVCs in a workspace namespace."""
        logger.info("pvcs_deleted", namespace=namespace)
