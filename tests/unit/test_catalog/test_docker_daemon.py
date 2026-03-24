from pyworkspace.catalog.runtime.docker_daemon import DockerDaemonService


class TestDockerDaemonService:
    def setup_method(self):
        self.svc = DockerDaemonService()

    def test_service_type(self):
        assert self.svc.service_type == "docker_daemon"

    def test_default_port(self):
        assert self.svc.default_port == 2375

    def test_env_vars(self):
        env = self.svc.get_env_vars("dind1", "ws.local", {}, {})
        assert env["DOCKER_HOST"] == "tcp://dind1.ws.local:2375"
        assert env["DOCKER_TLS_CERTDIR"] == ""

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "docker_build" in tools
        assert "docker_compose_up" in tools
        assert len(tools) == 12

    def test_health_check(self):
        hc = self.svc.get_health_check("dind1", "ws.local")
        assert hc["httpGet"]["path"] == "/_ping"

    def test_init_commands_empty(self):
        assert self.svc.get_init_commands({}) == []

    def test_generate_credentials_empty(self):
        assert self.svc.generate_credentials({}) == {}
