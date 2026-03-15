"""Secret injection into service pods as environment variables."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

class SecretInjector:
    """Injects secrets into K8s pods as environment variables."""

    def __init__(self, vault_client=None):
        self.vault = vault_client

    async def inject_into_pod_spec(
        self,
        pod_spec: dict,
        workspace_id: str,
        service_name: str,
    ) -> dict:
        """Add secret env vars to a pod spec."""
        if not self.vault:
            return pod_spec

        credentials = await self.vault.retrieve(workspace_id, service_name)
        if not credentials:
            return pod_spec

        containers = pod_spec.get("spec", {}).get("containers", [])
        for container in containers:
            env = container.setdefault("env", [])
            for key, value in credentials.items():
                env.append({"name": key.upper(), "value": str(value)})

        return pod_spec

    async def build_env_vars(self, workspace_id: str, services: list[dict]) -> dict[str, str]:
        """Collect all env vars from all services for agent injection."""
        env_vars = {}
        for svc in services:
            svc_env = svc.get("env_vars", {})
            env_vars.update(svc_env)
        return env_vars
