from pyworkspace.catalog.databases.mysql import MySQLService


class TestMySQLService:
    def setup_method(self):
        self.svc = MySQLService()

    def test_service_type(self):
        assert self.svc.service_type == "mysql"

    def test_default_port(self):
        assert self.svc.default_port == 3306

    def test_supported_versions(self):
        assert "8.0" in self.svc.supported_versions

    def test_docker_image(self):
        assert self.svc.get_docker_image("8.0") == "mysql:8.0"

    def test_env_vars(self):
        creds = {"user": "u", "password": "p", "database": "db", "root_password": "rp"}
        env = self.svc.get_env_vars("mysql1", "ws.local", creds, {})
        assert env["MYSQL_HOST"] == "mysql1.ws.local"
        assert env["MYSQL_ROOT_PASSWORD"] == "rp"
        assert "mysql://u:p@" in env["MYSQL_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "sql_query" in tools
        assert "db_list_tables" in tools

    def test_health_check(self):
        hc = self.svc.get_health_check("mysql1", "ws.local")
        assert hc["tcpSocket"]["port"] == 3306

    def test_init_commands(self):
        cmds = self.svc.get_init_commands({})
        assert len(cmds) == 1
        assert "utf8mb4" in cmds[0]

    def test_init_commands_custom_charset(self):
        cmds = self.svc.get_init_commands({"charset": "latin1"})
        assert "latin1" in cmds[0]

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "root_password" in creds
        assert "user" in creds
        assert "password" in creds
        assert creds["database"] == "pyws_db"
