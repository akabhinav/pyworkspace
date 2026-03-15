from __future__ import annotations

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class PrometheusService(ServiceDefinition):
    service_type = "prometheus"
    display_name = "Prometheus"
    description = "Time-series monitoring and alerting toolkit."
    default_version = "v2.48.0"
    supported_versions = ["v2.45.0", "v2.47.0", "v2.48.0"]
    docker_image_template = "prom/prometheus:{version}"
    default_port = 9090
    default_resources = ResourceSpec(cpu="0.5", memory="512Mi", disk="5Gi")
    categories = ["monitoring", "metrics"]

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
            "PROMETHEUS_URL": f"http://{host}:{port}",
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "prometheus_query",
            "prometheus_query_range",
            "prometheus_targets",
            "prometheus_alerts",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/-/healthy",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {}
