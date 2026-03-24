from pyworkspace.k8s.rbac_manager import RBACManager


class TestRBACManager:
    def setup_method(self):
        self.mgr = RBACManager()

    def test_build_service_account(self):
        sa = self.mgr.build_service_account("pyws-ws1", "ws-1")
        assert sa["kind"] == "ServiceAccount"
        assert sa["metadata"]["name"] == "workspace-agent"
        assert sa["metadata"]["namespace"] == "pyws-ws1"
        assert sa["metadata"]["labels"]["workspace"] == "ws-1"

    def test_build_role(self):
        role = self.mgr.build_role("pyws-ws1", "ws-1")
        assert role["kind"] == "Role"
        assert role["metadata"]["name"] == "workspace-role"
        assert len(role["rules"]) == 2
        # First rule: pods, services, configmaps
        assert "pods" in role["rules"][0]["resources"]

    def test_build_role_binding(self):
        rb = self.mgr.build_role_binding("pyws-ws1", "ws-1")
        assert rb["kind"] == "RoleBinding"
        assert rb["roleRef"]["name"] == "workspace-role"
        assert rb["subjects"][0]["name"] == "workspace-agent"
