from __future__ import annotations

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class MemcachedService(ServiceDefinition):
    service_type = "memcached"
    display_name = "Memcached"
    description = "High-performance distributed memory object caching system."
    default_version = "1.6"
    supported_versions = ["1.5", "1.6"]
    docker_image_template = "memcached:{version}"
    default_port = 11211
    default_resources = ResourceSpec(cpu="0.25", memory="256Mi", disk="0")
    categories = ["cache"]

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
            "MEMCACHED_HOST": host,
            "MEMCACHED_PORT": port,
            "MEMCACHED_URL": f"memcached://{host}:{port}",
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "memcached_get",
            "memcached_set",
            "memcached_delete",
            "memcached_stats",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {"tcpSocket": {"host": host, "port": self.default_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        # Memcached has no built-in authentication.
        return {}
