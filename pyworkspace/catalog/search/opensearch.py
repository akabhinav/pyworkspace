from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class OpenSearchService(ServiceDefinition):
    service_type = "opensearch"
    display_name = "OpenSearch"
    description = "Open-source search and analytics engine, fork of Elasticsearch."
    default_version = "2.11.0"
    supported_versions = ["2.9.0", "2.10.0", "2.11.0"]
    docker_image_template = "opensearchproject/opensearch:{version}"
    default_port = 9200
    default_resources = ResourceSpec(cpu="1", memory="2Gi", disk="10Gi")
    categories = ["search", "analytics"]

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        port = str(self.default_port)
        password = credentials.get("password", "")
        return {
            "OPENSEARCH_URL": f"https://{host}:{port}",
            "OPENSEARCH_HOST": host,
            "OPENSEARCH_PORT": port,
            "OPENSEARCH_USER": credentials.get("user", "admin"),
            "OPENSEARCH_PASSWORD": password,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "opensearch_search",
            "opensearch_index",
            "opensearch_delete",
            "opensearch_list_indices",
            "opensearch_mapping",
            "opensearch_aggregate",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/_cluster/health",
                "scheme": "HTTPS",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "user": "admin",
            "password": secrets_mod.token_urlsafe(24),
        }
