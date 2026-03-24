from pyworkspace.catalog.monitoring.grafana import GrafanaService


class TestGrafanaService:
    def setup_method(self):
        self.svc = GrafanaService()

    def test_service_type(self):
        assert self.svc.service_type == "grafana"

    def test_default_port(self):
        assert self.svc.default_port == 3000

    def test_env_vars(self):
        creds = {"user": "admin", "password": "secret"}
        env = self.svc.get_env_vars("graf1", "ws.local", creds, {})
        assert env["GRAFANA_USER"] == "admin"
        assert "http://" in env["GRAFANA_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "grafana_list_dashboards" in tools
        assert len(tools) == 3

    def test_health_check(self):
        hc = self.svc.get_health_check("graf1", "ws.local")
        assert hc["httpGet"]["path"] == "/api/health"

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert creds["user"] == "admin"
        assert "password" in creds
