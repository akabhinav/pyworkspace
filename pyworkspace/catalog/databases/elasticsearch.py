from __future__ import annotations

import secrets as secrets_mod
from typing import Any

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class ElasticsearchService(ServiceDefinition):
    service_type = "elasticsearch"
    display_name = "Elasticsearch"
    description = "Distributed search and analytics engine."
    default_version = "8.11.0"
    supported_versions = ["7.17.0", "8.8.0", "8.9.0", "8.10.0", "8.11.0"]
    docker_image_template = "docker.elastic.co/elasticsearch/elasticsearch:{version}"
    default_port = 9200
    default_resources = ResourceSpec(cpu="1", memory="2Gi", disk="10Gi")
    categories = ["database", "search"]

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        port = str(self.default_port)
        password = credentials["password"]
        return {
            "ELASTICSEARCH_URL": f"http://{host}:{port}",
            "ELASTICSEARCH_HOST": host,
            "ELASTICSEARCH_PORT": port,
            "ELASTICSEARCH_PASSWORD": password,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "es_search",
            "es_index",
            "es_delete",
            "es_list_indices",
            "es_mapping",
            "es_aggregate",
            "es_scroll",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/_cluster/health",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        return [
            "elasticsearch-plugin list",
        ]

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "user": "elastic",
            "password": secrets_mod.token_urlsafe(24),
        }

    def get_k8s_manifests(
        self,
        service_name: str,
        workspace_id: str,
        namespace: str,
        credentials: dict,
        config: dict,
        resources: ResourceSpec,
    ) -> list[dict]:
        manifests = super().get_k8s_manifests(
            service_name, workspace_id, namespace, credentials, config, resources
        )
        # Inject ES-specific environment variables into the deployment container
        deployment = manifests[0]
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        env = container.get("env", [])
        env.extend([
            {"name": "discovery.type", "value": "single-node"},
            {"name": "xpack.security.enabled", "value": "true"},
            {"name": "ELASTIC_PASSWORD", "value": credentials.get("password", "")},
            {"name": "ES_JAVA_OPTS", "value": "-Xms1g -Xmx1g"},
        ])
        container["env"] = env
        return manifests
