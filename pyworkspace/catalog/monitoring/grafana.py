from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class GrafanaService(ServiceDefinition):
    service_type = "grafana"
    display_name = "Grafana"
    description = "Observability dashboards for metrics, logs, and traces."
    default_version = "10.2.0"
    supported_versions = ["9.5.0", "10.0.0", "10.2.0"]
    docker_image_template = "grafana/grafana:{version}"
    default_port = 3000
    default_resources = ResourceSpec(cpu="0.25", memory="256Mi", disk="1Gi")
    categories = ["monitoring", "dashboards"]

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
            "GRAFANA_URL": f"http://{host}:{port}",
            "GRAFANA_USER": credentials.get("user", "admin"),
            "GRAFANA_PASSWORD": credentials["password"],
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "grafana_list_dashboards",
            "grafana_get_dashboard",
            "grafana_create_datasource",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/api/health",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "user": "admin",
            "password": secrets_mod.token_urlsafe(24),
        }
