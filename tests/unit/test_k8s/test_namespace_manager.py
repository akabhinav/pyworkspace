import pytest

from pyworkspace.k8s.namespace_manager import NamespaceManager


class TestNamespaceManager:
    @pytest.mark.asyncio
    async def test_create_namespace_no_client(self):
        mgr = NamespaceManager(k8s_client=None)
        # Should not raise - just skips
        await mgr.create_namespace("pyws-ws1", "ws-1")

    @pytest.mark.asyncio
    async def test_delete_namespace_no_client(self):
        mgr = NamespaceManager(k8s_client=None)
        await mgr.delete_namespace("pyws-ws1")

    @pytest.mark.asyncio
    async def test_namespace_exists_no_client(self):
        mgr = NamespaceManager(k8s_client=None)
        assert await mgr.namespace_exists("pyws-ws1") is False
