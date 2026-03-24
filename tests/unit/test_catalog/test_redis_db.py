from pyworkspace.catalog.databases.redis_db import RedisService


class TestRedisService:
    def setup_method(self):
        self.svc = RedisService()

    def test_service_type(self):
        assert self.svc.service_type == "redis"

    def test_default_port(self):
        assert self.svc.default_port == 6379

    def test_env_vars_with_password(self):
        creds = {"password": "secret"}
        env = self.svc.get_env_vars("redis1", "ws.local", creds, {})
        assert ":secret@" in env["REDIS_URL"]
        assert env["REDIS_HOST"] == "redis1.ws.local"

    def test_env_vars_no_password(self):
        env = self.svc.get_env_vars("redis1", "ws.local", {}, {})
        assert "redis://redis1.ws.local:6379/0" == env["REDIS_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "redis_get" in tools
        assert "redis_set" in tools
        assert len(tools) == 14

    def test_health_check(self):
        hc = self.svc.get_health_check("redis1", "ws.local")
        assert hc["tcpSocket"]["port"] == 6379

    def test_init_commands_with_maxmemory(self):
        cmds = self.svc.get_init_commands({"maxmemory": "512mb"})
        assert any("512mb" in c for c in cmds)

    def test_init_commands_default_policy(self):
        cmds = self.svc.get_init_commands({})
        assert any("allkeys-lru" in c for c in cmds)

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "password" in creds
