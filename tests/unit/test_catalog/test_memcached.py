from pyworkspace.catalog.cache.memcached import MemcachedService


class TestMemcachedService:
    def setup_method(self):
        self.svc = MemcachedService()

    def test_service_type(self):
        assert self.svc.service_type == "memcached"

    def test_default_port(self):
        assert self.svc.default_port == 11211

    def test_docker_image(self):
        assert self.svc.get_docker_image("1.6") == "memcached:1.6"

    def test_env_vars(self):
        env = self.svc.get_env_vars("mc1", "ws.local", {}, {})
        assert env["MEMCACHED_HOST"] == "mc1.ws.local"
        assert "memcached://" in env["MEMCACHED_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "memcached_get" in tools
        assert len(tools) == 4

    def test_health_check(self):
        hc = self.svc.get_health_check("mc1", "ws.local")
        assert hc["tcpSocket"]["port"] == 11211

    def test_init_commands_empty(self):
        assert self.svc.get_init_commands({}) == []

    def test_generate_credentials_empty(self):
        assert self.svc.generate_credentials({}) == {}
