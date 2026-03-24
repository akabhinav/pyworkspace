from pyworkspace.catalog.databases.neo4j import Neo4jService


class TestNeo4jService:
    def setup_method(self):
        self.svc = Neo4jService()

    def test_service_type(self):
        assert self.svc.service_type == "neo4j"

    def test_default_port(self):
        assert self.svc.default_port == 7474

    def test_docker_image(self):
        assert self.svc.get_docker_image("5") == "neo4j:5"

    def test_env_vars(self):
        creds = {"user": "neo4j", "password": "secret"}
        env = self.svc.get_env_vars("neo1", "ws.local", creds, {})
        assert "bolt://" in env["NEO4J_URI"]
        assert "7687" in env["NEO4J_URI"]
        assert "http://" in env["NEO4J_HTTP_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "cypher_query" in tools
        assert len(tools) == 3

    def test_health_check(self):
        hc = self.svc.get_health_check("neo1", "ws.local")
        assert hc["tcpSocket"]["port"] == 7687

    def test_init_commands_empty(self):
        assert self.svc.get_init_commands({}) == []

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert creds["user"] == "neo4j"
        assert "password" in creds
