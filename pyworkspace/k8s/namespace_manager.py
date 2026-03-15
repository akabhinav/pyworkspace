"""K8s namespace management — one namespace per workspace."""
from __future__ import annotations
import structlog
from pyworkspace.config.settings import get_settings

logger = structlog.get_logger()

class NamespaceManager:
    """Creates, deletes, and manages K8s namespaces for workspaces."""

    def __init__(self, k8s_client=None):
        self._client = k8s_client
        self._api = None

    async def initialize(self) -> None:
        """Initialize K8s API client."""
        if self._client:
            return
        try:
            from kubernetes import client, config as k8s_config
            settings = get_settings()
            if settings.K8S_IN_CLUSTER:
                k8s_config.load_incluster_config()
            else:
                k8s_config.load_kube_config(config_file=settings.K8S_KUBECONFIG_PATH)
            self._api = client.CoreV1Api()
            self._apps_api = client.AppsV1Api()
            self._networking_api = client.NetworkingV1Api()
            logger.info("k8s_client_initialized")
        except Exception as e:
            logger.warning("k8s_client_init_failed", error=str(e))

    async def create_namespace(self, namespace: str, workspace_id: str) -> None:
        """Create a K8s namespace for a workspace."""
        if not self._api:
            logger.info("k8s_namespace_create_skipped", namespace=namespace, reason="no_client")
            return
        from kubernetes import client
        body = client.V1Namespace(
            metadata=client.V1ObjectMeta(
                name=namespace,
                labels={
                    "app": "pyworkspace",
                    "workspace": workspace_id,
                    "managed-by": "pyworkspace",
                },
            )
        )
        self._api.create_namespace(body=body)
        logger.info("k8s_namespace_created", namespace=namespace)

    async def delete_namespace(self, namespace: str) -> None:
        if not self._api:
            return
        self._api.delete_namespace(name=namespace)
        logger.info("k8s_namespace_deleted", namespace=namespace)

    async def namespace_exists(self, namespace: str) -> bool:
        if not self._api:
            return False
        try:
            self._api.read_namespace(name=namespace)
            return True
        except Exception:
            return False
