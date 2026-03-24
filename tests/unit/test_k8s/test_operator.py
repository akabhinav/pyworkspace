import pytest

from pyworkspace.k8s.operator import WorkspaceOperator


class TestWorkspaceOperator:
    def test_has_all_managers(self):
        op = WorkspaceOperator()
        assert op.namespace_mgr is not None
        assert op.pod_mgr is not None
        assert op.pvc_mgr is not None
        assert op.rbac_mgr is not None

    @pytest.mark.asyncio
    async def test_setup_rbac(self):
        op = WorkspaceOperator()
        manifests = await op.setup_rbac("pyws-ws1", "ws-1")
        assert len(manifests) == 3
        kinds = [m["kind"] for m in manifests]
        assert "ServiceAccount" in kinds
        assert "Role" in kinds
        assert "RoleBinding" in kinds
