from __future__ import annotations

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class LokiService(ServiceDefinition):
    service_type = "loki"
    display_name = "Grafana Loki"
    description = "Log aggregation system inspired by Prometheus."
    default_version = "2.9.0"
    supported_versions = ["2.8.0", "2.9.0"]
    docker_image_template = "grafana/loki:{version}"
    default_port = 3100
    default_resources = ResourceSpec(cpu="0.25", memory="256Mi", disk="5Gi")
    categories = ["monitoring", "logging"]

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        port = str(self.default_port)
        return {
            "LOKI_URL": f"http://{host}:{port}",
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "loki_query",
            "loki_push",
            "loki_labels",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/ready",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {}
