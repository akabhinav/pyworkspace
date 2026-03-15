from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class Neo4jService(ServiceDefinition):
    service_type = "neo4j"
    display_name = "Neo4j"
    description = "Graph database with Cypher query language."
    default_version = "5"
    supported_versions = ["4.4", "5"]
    docker_image_template = "neo4j:{version}"
    default_port = 7474
    default_resources = ResourceSpec(cpu="0.5", memory="1Gi", disk="5Gi")
    categories = ["database", "graph"]

    _bolt_port = 7687

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        password = credentials["password"]
        return {
            "NEO4J_URI": f"bolt://{host}:{self._bolt_port}",
            "NEO4J_HTTP_URL": f"http://{host}:{self.default_port}",
            "NEO4J_USER": credentials.get("user", "neo4j"),
            "NEO4J_PASSWORD": password,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "cypher_query",
            "neo4j_list_labels",
            "neo4j_list_relationships",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {"tcpSocket": {"host": host, "port": self._bolt_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "user": "neo4j",
            "password": secrets_mod.token_urlsafe(24),
        }
