from pyworkspace.catalog.monitoring.loki import LokiService


class TestLokiService:
    def setup_method(self):
        self.svc = LokiService()

    def test_service_type(self):
        assert self.svc.service_type == "loki"

    def test_default_port(self):
        assert self.svc.default_port == 3100

    def test_env_vars(self):
        env = self.svc.get_env_vars("loki1", "ws.local", {}, {})
        assert "http://loki1.ws.local:3100" == env["LOKI_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "loki_query" in tools
        assert len(tools) == 3

    def test_health_check(self):
        hc = self.svc.get_health_check("loki1", "ws.local")
        assert hc["httpGet"]["path"] == "/ready"

    def test_generate_credentials_empty(self):
        assert self.svc.generate_credentials({}) == {}
