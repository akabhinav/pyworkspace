from pyworkspace.catalog.cache.redis_cache import RedisCacheService


class TestRedisCacheService:
    def setup_method(self):
        self.svc = RedisCacheService()

    def test_service_type(self):
        assert self.svc.service_type == "redis_cache"

    def test_default_port(self):
        assert self.svc.default_port == 6379

    def test_env_vars(self):
        creds = {"password": "secret"}
        env = self.svc.get_env_vars("cache1", "ws.local", creds, {})
        assert "REDIS_CACHE_URL" in env
        assert ":secret@" in env["REDIS_CACHE_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "cache_get" in tools
        assert "cache_flush" in tools
        assert len(tools) == 5

    def test_init_commands(self):
        cmds = self.svc.get_init_commands({})
        assert len(cmds) == 2
        assert any("256mb" in c for c in cmds)
        assert any("allkeys-lru" in c for c in cmds)

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "password" in creds
