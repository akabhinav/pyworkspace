from pyworkspace.catalog.databases.cassandra import CassandraService


class TestCassandraService:
    def setup_method(self):
        self.svc = CassandraService()

    def test_service_type(self):
        assert self.svc.service_type == "cassandra"

    def test_default_port(self):
        assert self.svc.default_port == 9042

    def test_docker_image(self):
        assert self.svc.get_docker_image("4.1") == "cassandra:4.1"

    def test_env_vars(self):
        creds = {"user": "u", "password": "p", "keyspace": "ks"}
        env = self.svc.get_env_vars("cass1", "ws.local", creds, {})
        assert env["CASSANDRA_HOST"] == "cass1.ws.local"
        assert env["CASSANDRA_KEYSPACE"] == "ks"

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "cql_query" in tools
        assert len(tools) == 4

    def test_health_check(self):
        hc = self.svc.get_health_check("cass1", "ws.local")
        assert hc["tcpSocket"]["port"] == 9042

    def test_init_commands(self):
        cmds = self.svc.get_init_commands({"keyspace": "myks", "replication_factor": 3})
        assert len(cmds) == 1
        assert "myks" in cmds[0]
        assert "3" in cmds[0]

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "user" in creds
        assert creds["keyspace"] == "pyws_keyspace"
