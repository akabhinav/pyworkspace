from pyworkspace.catalog.databases.clickhouse import ClickHouseService


class TestClickHouseService:
    def setup_method(self):
        self.svc = ClickHouseService()

    def test_service_type(self):
        assert self.svc.service_type == "clickhouse"

    def test_default_port(self):
        assert self.svc.default_port == 8123

    def test_docker_image(self):
        assert self.svc.get_docker_image("23.8") == "clickhouse/clickhouse-server:23.8"

    def test_env_vars(self):
        creds = {"database": "db"}
        env = self.svc.get_env_vars("ch1", "ws.local", creds, {})
        assert env["CLICKHOUSE_HOST"] == "ch1.ws.local"
        assert env["CLICKHOUSE_HTTP_PORT"] == "8123"
        assert env["CLICKHOUSE_NATIVE_PORT"] == "9000"
        assert "http://" in env["CLICKHOUSE_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "sql_query" in tools
        assert "db_list_tables" in tools

    def test_health_check(self):
        hc = self.svc.get_health_check("ch1", "ws.local")
        assert hc["httpGet"]["path"] == "/ping"

    def test_init_commands(self):
        cmds = self.svc.get_init_commands({"database": "analytics"})
        assert "analytics" in cmds[0]

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert creds["user"] == "default"
        assert "password" in creds
