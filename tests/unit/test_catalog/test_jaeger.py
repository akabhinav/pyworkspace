from pyworkspace.catalog.monitoring.jaeger import JaegerService


class TestJaegerService:
    def setup_method(self):
        self.svc = JaegerService()

    def test_service_type(self):
        assert self.svc.service_type == "jaeger"

    def test_default_port(self):
        assert self.svc.default_port == 16686

    def test_docker_image(self):
        assert "all-in-one" in self.svc.get_docker_image("1.51")

    def test_env_vars(self):
        env = self.svc.get_env_vars("jaeger1", "ws.local", {}, {})
        assert "JAEGER_URL" in env
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" in env
        assert "4317" in env["OTEL_EXPORTER_OTLP_ENDPOINT"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "jaeger_search_traces" in tools
        assert len(tools) == 3

    def test_health_check(self):
        hc = self.svc.get_health_check("jaeger1", "ws.local")
        assert hc["httpGet"]["port"] == 16686

    def test_generate_credentials_empty(self):
        assert self.svc.generate_credentials({}) == {}
