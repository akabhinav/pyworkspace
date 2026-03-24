from pyworkspace.catalog.databases.sqlite import SQLiteService
from pyworkspace.core.specs import ResourceSpec


class TestSQLiteService:
    def setup_method(self):
        self.svc = SQLiteService()

    def test_service_type(self):
        assert self.svc.service_type == "sqlite"

    def test_default_port_zero(self):
        assert self.svc.default_port == 0

    def test_env_vars(self):
        env = self.svc.get_env_vars("db1", "ws.local", {}, {})
        assert env["SQLITE_PATH"] == "/data/db1.db"

    def test_env_vars_custom_path(self):
        env = self.svc.get_env_vars("db1", "ws.local", {}, {"path": "/custom/my.db"})
        assert env["SQLITE_PATH"] == "/custom/my.db"

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "sql_query" in tools
        assert "sql_migrate" in tools

    def test_health_check_empty(self):
        assert self.svc.get_health_check("db1", "ws.local") == {}

    def test_generate_credentials_empty(self):
        assert self.svc.generate_credentials({}) == {}

    def test_k8s_manifests_empty(self):
        manifests = self.svc.get_k8s_manifests(
            "db1", "ws-1", "ns1", {}, {}, ResourceSpec()
        )
        assert manifests == []
