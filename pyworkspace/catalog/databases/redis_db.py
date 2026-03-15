from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class RedisService(ServiceDefinition):
    service_type = "redis"
    display_name = "Redis"
    description = "In-memory data store used as database, cache, and message broker."
    default_version = "7"
    supported_versions = ["6", "7"]
    docker_image_template = "redis:{version}"
    default_port = 6379
    default_resources = ResourceSpec(cpu="0.25", memory="256Mi", disk="1Gi")
    categories = ["database", "cache", "nosql"]

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
            "REDIS_URL": url,
            "REDIS_HOST": host,
            "REDIS_PORT": port,
            "REDIS_PASSWORD": password,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "redis_get",
            "redis_set",
            "redis_delete",
            "redis_scan",
            "redis_hget",
            "redis_hset",
            "redis_lpush",
            "redis_lrange",
            "redis_zadd",
            "redis_zrange",
            "redis_publish",
            "redis_subscribe",
            "redis_ttl",
            "redis_flush_db",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {"tcpSocket": {"host": host, "port": self.default_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        maxmemory = config.get("maxmemory")
        if maxmemory:
            commands.append(f"redis-cli CONFIG SET maxmemory {maxmemory}")
        policy = config.get("maxmemory_policy", "allkeys-lru")
        commands.append(f"redis-cli CONFIG SET maxmemory-policy {policy}")
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "password": secrets_mod.token_urlsafe(24),
        }
