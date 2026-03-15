"""Pod lifecycle management for workspace services."""
from __future__ import annotations
import asyncio
import structlog

logger = structlog.get_logger()

class PodManager:
    """Manages pod lifecycle for workspace services."""

    def __init__(self, k8s_client=None):
        self._client = k8s_client
        self._api = None
        self._apps_api = None

    async def initialize(self) -> None:
        if self._client:
            return
        try:
            from kubernetes import client, config as k8s_config
            from pyworkspace.config.settings import get_settings
            settings = get_settings()
            if settings.K8S_IN_CLUSTER:
                k8s_config.load_incluster_config()
            else:
                k8s_config.load_kube_config(config_file=settings.K8S_KUBECONFIG_PATH)
            self._api = client.CoreV1Api()
            self._apps_api = client.AppsV1Api()
        except Exception as e:
            logger.warning("k8s_pod_manager_init_failed", error=str(e))

    async def apply_manifest(self, manifest: dict) -> None:
        """Apply a K8s manifest (Deployment, Service, PVC, etc.)."""
        if not self._api:
            logger.info("k8s_manifest_apply_skipped", kind=manifest.get("kind"), reason="no_client")
            return

        kind = manifest.get("kind", "")
        namespace = manifest.get("metadata", {}).get("namespace", "default")
        name = manifest.get("metadata", {}).get("name", "")

        from kubernetes import client, utils

        if kind == "Deployment":
            body = client.V1Deployment(**manifest)  # simplified
            try:
                self._apps_api.create_namespaced_deployment(namespace=namespace, body=manifest)
            except Exception:
                self._apps_api.patch_namespaced_deployment(name=name, namespace=namespace, body=manifest)
        elif kind == "Service":
            try:
                self._api.create_namespaced_service(namespace=namespace, body=manifest)
            except Exception:
                self._api.patch_namespaced_service(name=name, namespace=namespace, body=manifest)
        elif kind == "PersistentVolumeClaim":
            try:
                self._api.create_namespaced_persistent_volume_claim(namespace=namespace, body=manifest)
            except Exception:
                pass  # PVCs are immutable after creation
        elif kind == "NetworkPolicy":
            from kubernetes import client as k8s_client
            networking_api = k8s_client.NetworkingV1Api()
            try:
                networking_api.create_namespaced_network_policy(namespace=namespace, body=manifest)
            except Exception:
                networking_api.patch_namespaced_network_policy(name=name, namespace=namespace, body=manifest)
        elif kind == "Ingress":
            from kubernetes import client as k8s_client
            networking_api = k8s_client.NetworkingV1Api()
            try:
                networking_api.create_namespaced_ingress(namespace=namespace, body=manifest)
            except Exception:
                networking_api.patch_namespaced_ingress(name=name, namespace=namespace, body=manifest)

        logger.info("k8s_manifest_applied", kind=kind, name=name, namespace=namespace)

    async def wait_for_healthy(self, namespace: str, service_name: str, timeout_seconds: int = 300) -> bool:
        """Wait for a deployment's pods to be ready."""
        if not self._apps_api:
            return True

        deadline = asyncio.get_event_loop().time() + timeout_seconds
        while asyncio.get_event_loop().time() < deadline:
            try:
                deployment = self._apps_api.read_namespaced_deployment(name=service_name, namespace=namespace)
                ready = deployment.status.ready_replicas or 0
                desired = deployment.spec.replicas or 1
                if ready >= desired:
                    logger.info("service_healthy", namespace=namespace, service=service_name)
                    return True
            except Exception:
                pass
            await asyncio.sleep(2)

        logger.warning("service_health_timeout", namespace=namespace, service=service_name)
        return False

    async def wait_for_namespace_healthy(self, namespace: str, timeout_seconds: int = 90) -> bool:
        """Wait for all deployments in a namespace to be ready."""
        if not self._apps_api:
            return True

        deadline = asyncio.get_event_loop().time() + timeout_seconds
        while asyncio.get_event_loop().time() < deadline:
            try:
                deployments = self._apps_api.list_namespaced_deployment(namespace=namespace)
                all_ready = all(
                    (d.status.ready_replicas or 0) >= (d.spec.replicas or 1)
                    for d in deployments.items
                )
                if all_ready:
                    return True
            except Exception:
                pass
            await asyncio.sleep(2)
        return False

    async def scale_namespace_deployments(self, namespace: str, replicas: int) -> None:
        """Scale all deployments in a namespace."""
        if not self._apps_api:
            return
        deployments = self._apps_api.list_namespaced_deployment(namespace=namespace)
        for dep in deployments.items:
            dep.spec.replicas = replicas
            self._apps_api.patch_namespaced_deployment(
                name=dep.metadata.name, namespace=namespace, body=dep
            )
        logger.info("namespace_scaled", namespace=namespace, replicas=replicas)

    async def apply_network_policy(self, namespace: str, workspace_id: str, egress_allowed: bool) -> None:
        """Apply network isolation policy to workspace namespace."""
        from pyworkspace.networking.network_policy import build_network_policy
        policy = build_network_policy(namespace, workspace_id, egress_allowed)
        await self.apply_manifest(policy)

    async def get_namespace_resource_metrics(self, namespace: str) -> dict:
        """Get resource usage metrics for a namespace."""
        # In production this would query metrics-server API
        return {"cpu_cores": 0.0, "memory_gib": 0.0, "disk_gib": 0.0}
