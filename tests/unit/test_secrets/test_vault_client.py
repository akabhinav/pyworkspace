import pytest

from pyworkspace.secrets.vault_client import VaultClient


class TestVaultClient:
    @pytest.mark.asyncio
    async def test_store_without_client(self):
        vc = VaultClient()
        # No hvac, so _client is None
        await vc.store("ws-1", "pg1", {"user": "u", "password": "p"})

    @pytest.mark.asyncio
    async def test_retrieve_without_client(self):
        vc = VaultClient()
        result = await vc.retrieve("ws-1", "pg1")
        assert result == {}

    @pytest.mark.asyncio
    async def test_delete_without_client(self):
        vc = VaultClient()
        await vc.delete("ws-1", "pg1")

    @pytest.mark.asyncio
    async def test_delete_workspace_secrets_without_client(self):
        vc = VaultClient()
        await vc.delete_workspace_secrets("ws-1")
