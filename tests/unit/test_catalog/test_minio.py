from pyworkspace.catalog.cloud.minio import MinIOService


class TestMinIOService:
    def setup_method(self):
        self.svc = MinIOService()

    def test_service_type(self):
        assert self.svc.service_type == "minio"

    def test_default_port(self):
        assert self.svc.default_port == 9000

    def test_env_vars(self):
        creds = {"access_key": "ak", "secret_key": "sk"}
        env = self.svc.get_env_vars("minio1", "ws.local", creds, {})
        assert env["MINIO_ACCESS_KEY"] == "ak"
        assert env["MINIO_SECRET_KEY"] == "sk"
        assert "http://" in env["S3_ENDPOINT_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "s3_list_buckets" in tools
        assert "s3_put_object" in tools
        assert len(tools) == 6

    def test_health_check(self):
        hc = self.svc.get_health_check("minio1", "ws.local")
        assert hc["httpGet"]["path"] == "/minio/health/live"

    def test_init_commands_with_buckets(self):
        cmds = self.svc.get_init_commands({"buckets": ["data", "logs"]})
        assert len(cmds) == 2
        assert "local/data" in cmds[0]

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "access_key" in creds
        assert "secret_key" in creds
