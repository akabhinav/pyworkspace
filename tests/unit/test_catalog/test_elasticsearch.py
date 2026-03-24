from pyworkspace.catalog.databases.elasticsearch import ElasticsearchService
from pyworkspace.core.specs import ResourceSpec


class TestElasticsearchService:
    def setup_method(self):
        self.svc = ElasticsearchService()

    def test_service_type(self):
        assert self.svc.service_type == "elasticsearch"

    def test_default_port(self):
        assert self.svc.default_port == 9200

    def test_docker_image(self):
        img = self.svc.get_docker_image("8.11.0")
        assert "docker.elastic.co" in img

    def test_env_vars(self):
        creds = {"password": "secret"}
        env = self.svc.get_env_vars("es1", "ws.local", creds, {})
        assert env["ELASTICSEARCH_HOST"] == "es1.ws.local"
        assert env["ELASTICSEARCH_PASSWORD"] == "secret"

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "es_search" in tools
        assert "es_index" in tools
        assert len(tools) == 7

    def test_health_check(self):
        hc = self.svc.get_health_check("es1", "ws.local")
        assert hc["httpGet"]["path"] == "/_cluster/health"

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert creds["user"] == "elastic"
        assert "password" in creds

    def test_k8s_manifests_has_es_env(self):
        creds = {"password": "secret"}
        manifests = self.svc.get_k8s_manifests(
            "es1", "ws-1", "ns1", creds, {}, ResourceSpec()
        )
        deployment = manifests[0]
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        env_names = [e["name"] for e in container["env"]]
        assert "discovery.type" in env_names
        assert "xpack.security.enabled" in env_names
