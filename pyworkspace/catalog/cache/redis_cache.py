from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class RedisCacheService(ServiceDefinition):
    service_type = "redis_cache"
    display_name = "Redis Cache"
    description = "Redis instance optimised for caching with volatile eviction policies."
    default_version = "7"
    supported_versions = ["6", "7"]
    docker_image_template = "redis:{version}"
    default_port = 6379
    default_resources = ResourceSpec(cpu="0.25", memory="256Mi", disk="1Gi")
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
        password = credentials.get("password", "")
        url = f"redis://:{password}@{host}:{port}/0" if password else f"redis://{host}:{port}/0"
        return {
            "REDIS_CACHE_URL": url,
            "REDIS_CACHE_HOST": host,
            "REDIS_CACHE_PORT": port,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "cache_get",
            "cache_set",
            "cache_delete",
            "cache_flush",
            "cache_stats",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {"tcpSocket": {"host": host, "port": self.default_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        maxmemory = config.get("maxmemory", "256mb")
        policy = config.get("maxmemory_policy", "allkeys-lru")
        return [
            f"redis-cli CONFIG SET maxmemory {maxmemory}",
            f"redis-cli CONFIG SET maxmemory-policy {policy}",
        ]

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "password": secrets_mod.token_urlsafe(24),
        }
