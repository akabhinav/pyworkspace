from pyworkspace.catalog.databases.mongodb import MongoDBService


class TestMongoDBService:
    def setup_method(self):
        self.svc = MongoDBService()

    def test_service_type(self):
        assert self.svc.service_type == "mongodb"

    def test_default_port(self):
        assert self.svc.default_port == 27017

    def test_default_version(self):
        assert self.svc.default_version == "7"

    def test_supported_versions(self):
        assert "5" in self.svc.supported_versions
        assert "7" in self.svc.supported_versions

    def test_docker_image(self):
        assert self.svc.get_docker_image("7") == "mongo:7"

    def test_env_vars(self):
        creds = {"user": "u", "password": "p", "database": "db"}
        env = self.svc.get_env_vars("mongo1", "ws.local", creds, {})
        assert "MONGODB_URI" in env
        assert "mongodb://u:p@" in env["MONGODB_URI"]
        assert env["MONGODB_HOST"] == "mongo1.ws.local"
        assert env["MONGODB_PORT"] == "27017"

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "mongo_query" in tools
        assert "mongo_insert" in tools
        assert len(tools) == 7

    def test_health_check(self):
        hc = self.svc.get_health_check("mongo1", "ws.local")
        assert hc["tcpSocket"]["port"] == 27017

    def test_init_commands_with_collections(self):
        cmds = self.svc.get_init_commands({"collections": ["users", "orders"]})
        assert len(cmds) == 2
        assert "users" in cmds[0]

    def test_init_commands_empty(self):
        assert self.svc.get_init_commands({}) == []

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "user" in creds
        assert "password" in creds
        assert creds["database"] == "pyws_db"

    def test_generate_credentials_custom_db(self):
        creds = self.svc.generate_credentials({"database": "mydb"})
        assert creds["database"] == "mydb"
