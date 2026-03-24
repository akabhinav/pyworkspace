from ui.api_client import PyWorkspaceClient


class TestPyWorkspaceClient:
    def setup_method(self):
        self.client = PyWorkspaceClient(base_url="http://localhost:9999/v1")

    def test_default_base_url(self):
        c = PyWorkspaceClient()
        assert "v1" in c.base or "8000" in c.base

    def test_list_workspaces_fallback(self):
        # Should return demo data when API is unreachable
        result = self.client.list_workspaces()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_list_catalog_fallback(self):
        result = self.client.list_catalog()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_list_templates_fallback(self):
        result = self.client.list_templates()
        assert isinstance(result, list)

    def test_list_plugins_fallback(self):
        result = self.client.list_plugins()
        assert isinstance(result, list)

    def test_get_workspace_fallback(self):
        result = self.client.get_workspace("demo-ws-1")
        # Returns demo data or None
        assert result is None or isinstance(result, dict)

    def test_list_snapshots_fallback(self):
        result = self.client.list_snapshots("ws-1")
        assert isinstance(result, list)
