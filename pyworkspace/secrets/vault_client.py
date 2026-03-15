"""HashiCorp Vault client for workspace secret management."""
from __future__ import annotations
import structlog
from pyworkspace.config.settings import get_settings

logger = structlog.get_logger()

class VaultClient:
    """Manages secrets in HashiCorp Vault."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None

    async def connect(self) -> None:
        """Initialize Vault client connection."""
        try:
            import hvac
            self._client = hvac.Client(
                url=self.settings.VAULT_ADDR,
                token=self.settings.VAULT_TOKEN.get_secret_value(),
            )
            if self._client.is_authenticated():
                logger.info("vault_connected", addr=self.settings.VAULT_ADDR)
            else:
                logger.warning("vault_auth_failed")
                self._client = None
        except Exception as e:
            logger.warning("vault_connection_failed", error=str(e))
            self._client = None

    async def store(self, workspace_id: str, service_name: str, credentials: dict) -> None:
        """Store service credentials in Vault."""
        path = f"{self.settings.VAULT_WORKSPACE_PATH}/{workspace_id}/{service_name}"
        if self._client:
            self._client.secrets.kv.v2.create_or_update_secret(path=path, secret=credentials)
        logger.info("vault_secret_stored", workspace_id=workspace_id, service=service_name)

    async def retrieve(self, workspace_id: str, service_name: str) -> dict:
        """Retrieve service credentials from Vault."""
        path = f"{self.settings.VAULT_WORKSPACE_PATH}/{workspace_id}/{service_name}"
        if self._client:
            response = self._client.secrets.kv.v2.read_secret_version(path=path)
            return response["data"]["data"]
        return {}

    async def delete(self, workspace_id: str, service_name: str) -> None:
        """Delete service credentials."""
        path = f"{self.settings.VAULT_WORKSPACE_PATH}/{workspace_id}/{service_name}"
        if self._client:
            self._client.secrets.kv.v2.delete_metadata_and_all_versions(path=path)

    async def delete_workspace_secrets(self, workspace_id: str) -> None:
        """Delete all secrets for a workspace."""
        path = f"{self.settings.VAULT_WORKSPACE_PATH}/{workspace_id}"
        if self._client:
            try:
                keys = self._client.secrets.kv.v2.list_secrets(path=path)
                for key in keys.get("data", {}).get("keys", []):
                    await self.delete(workspace_id, key.rstrip("/"))
            except Exception:
                pass  # Path may not exist
        logger.info("vault_workspace_secrets_deleted", workspace_id=workspace_id)

    async def rotate(self, workspace_id: str, service_name: str) -> dict:
        """Rotate credentials for a service."""
        from pyworkspace.secrets.generator import CredentialGenerator
        old = await self.retrieve(workspace_id, service_name)
        new_creds = CredentialGenerator.generate(service_name, old)
        await self.store(workspace_id, service_name, new_creds)
        logger.info("vault_secret_rotated", workspace_id=workspace_id, service=service_name)
        return new_creds
