from __future__ import annotations

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class JaegerService(ServiceDefinition):
    service_type = "jaeger"
    display_name = "Jaeger"
    description = "Distributed tracing backend with OpenTelemetry support."
    default_version = "1.51"
    supported_versions = ["1.49", "1.50", "1.51"]
    docker_image_template = "jaegertracing/all-in-one:{version}"
    default_port = 16686
    default_resources = ResourceSpec(cpu="0.5", memory="512Mi", disk="2Gi")
    categories = ["monitoring", "tracing"]

    _otlp_grpc_port = 4317
    _otlp_http_port = 4318

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "JAEGER_URL": f"http://{host}:{self.default_port}",
            "OTEL_EXPORTER_OTLP_ENDPOINT": f"http://{host}:{self._otlp_grpc_port}",
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "jaeger_search_traces",
            "jaeger_get_trace",
            "jaeger_list_services",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {}
