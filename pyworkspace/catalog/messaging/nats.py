from __future__ import annotations

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class NATSService(ServiceDefinition):
    service_type = "nats"
    display_name = "NATS"
    description = "High-performance cloud-native messaging system."
    default_version = "2.10"
    supported_versions = ["2.9", "2.10"]
    docker_image_template = "nats:{version}"
    default_port = 4222
    default_resources = ResourceSpec(cpu="0.25", memory="128Mi", disk="1Gi")
    categories = ["messaging"]

    _monitoring_port = 8222

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
            "NATS_URL": f"nats://{host}:{port}",
            "NATS_HOST": host,
            "NATS_PORT": port,
            "NATS_MONITORING_URL": f"http://{host}:{self._monitoring_port}",
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "nats_publish",
            "nats_subscribe",
            "nats_request",
            "nats_stream_list",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self._monitoring_port,
                "path": "/healthz",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        # NATS uses token/nkey auth configured at server level; no user/pass by default.
        return {}
