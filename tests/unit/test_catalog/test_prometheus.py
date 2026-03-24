from pyworkspace.catalog.monitoring.prometheus import PrometheusService


class TestPrometheusService:
    def setup_method(self):
        self.svc = PrometheusService()

    def test_service_type(self):
        assert self.svc.service_type == "prometheus"

    def test_default_port(self):
        assert self.svc.default_port == 9090

    def test_env_vars(self):
        env = self.svc.get_env_vars("prom1", "ws.local", {}, {})
        assert "http://prom1.ws.local:9090" == env["PROMETHEUS_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "prometheus_query" in tools
        assert "prometheus_alerts" in tools
        assert len(tools) == 4

    def test_health_check(self):
        hc = self.svc.get_health_check("prom1", "ws.local")
        assert hc["httpGet"]["path"] == "/-/healthy"

    def test_generate_credentials_empty(self):
        assert self.svc.generate_credentials({}) == {}
