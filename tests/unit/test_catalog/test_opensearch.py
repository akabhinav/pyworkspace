from pyworkspace.catalog.search.opensearch import OpenSearchService


class TestOpenSearchService:
    def setup_method(self):
        self.svc = OpenSearchService()

    def test_service_type(self):
        assert self.svc.service_type == "opensearch"

    def test_default_port(self):
        assert self.svc.default_port == 9200

    def test_docker_image(self):
        assert "opensearchproject" in self.svc.get_docker_image("2.11.0")

    def test_env_vars(self):
        creds = {"user": "admin", "password": "secret"}
        env = self.svc.get_env_vars("os1", "ws.local", creds, {})
        assert "https://" in env["OPENSEARCH_URL"]
        assert env["OPENSEARCH_USER"] == "admin"

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "opensearch_search" in tools
        assert len(tools) == 6

    def test_health_check(self):
        hc = self.svc.get_health_check("os1", "ws.local")
        assert hc["httpGet"]["scheme"] == "HTTPS"

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert creds["user"] == "admin"
        assert "password" in creds
