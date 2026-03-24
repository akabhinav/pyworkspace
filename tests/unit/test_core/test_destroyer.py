import pytest
from unittest.mock import AsyncMock

from pyworkspace.core.destroyer import WorkspaceDestroyer


class TestWorkspaceDestroyer:
    @pytest.mark.asyncio
    async def test_destroy_without_managers(self):
        destroyer = WorkspaceDestroyer()
        workspace = {
            "id": "ws-1",
            "k8s_namespace": "pyws-ws1",
            "dns_zone": "ws1.local",
            "status": "running",
        }
        result = await destroyer.destroy(workspace)
        assert result["status"] == "destroyed"
        assert result["updated_at"] is not None

    @pytest.mark.asyncio
    async def test_destroy_calls_k8s(self):
        k8s = AsyncMock()
        destroyer = WorkspaceDestroyer(k8s_manager=k8s)
        workspace = {"id": "ws-1", "k8s_namespace": "pyws-ws1", "dns_zone": None}
        await destroyer.destroy(workspace)
        k8s.delete_namespace.assert_awaited_once_with("pyws-ws1")

    @pytest.mark.asyncio
    async def test_destroy_calls_secrets(self):
        secrets = AsyncMock()
        destroyer = WorkspaceDestroyer(secret_manager=secrets)
        workspace = {"id": "ws-1", "k8s_namespace": None, "dns_zone": None}
        await destroyer.destroy(workspace)
        secrets.delete_workspace_secrets.assert_awaited_once_with("ws-1")

    @pytest.mark.asyncio
    async def test_destroy_calls_dns(self):
        dns = AsyncMock()
        destroyer = WorkspaceDestroyer(dns_manager=dns)
        workspace = {"id": "ws-1", "k8s_namespace": None, "dns_zone": "ws1.local"}
        await destroyer.destroy(workspace)
        dns.remove_zone.assert_awaited_once_with("ws1.local")
