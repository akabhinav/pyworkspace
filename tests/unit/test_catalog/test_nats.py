from pyworkspace.catalog.messaging.nats import NATSService


class TestNATSService:
    def setup_method(self):
        self.svc = NATSService()

    def test_service_type(self):
        assert self.svc.service_type == "nats"

    def test_default_port(self):
        assert self.svc.default_port == 4222

    def test_docker_image(self):
        assert self.svc.get_docker_image("2.10") == "nats:2.10"

    def test_env_vars(self):
        env = self.svc.get_env_vars("nats1", "ws.local", {}, {})
        assert "nats://nats1.ws.local:4222" == env["NATS_URL"]
        assert "8222" in env["NATS_MONITORING_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "nats_publish" in tools
        assert len(tools) == 4

    def test_health_check(self):
        hc = self.svc.get_health_check("nats1", "ws.local")
        assert hc["httpGet"]["path"] == "/healthz"
        assert hc["httpGet"]["port"] == 8222

    def test_init_commands_empty(self):
        assert self.svc.get_init_commands({}) == []

    def test_generate_credentials_empty(self):
        assert self.svc.generate_credentials({}) == {}
