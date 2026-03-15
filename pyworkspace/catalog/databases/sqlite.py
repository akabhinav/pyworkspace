from __future__ import annotations

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class SQLiteService(ServiceDefinition):
    service_type = "sqlite"
    display_name = "SQLite"
    description = "Lightweight file-based relational database — no server required."
    default_version = "3"
    supported_versions = ["3"]
    docker_image_template = ""
    default_port = 0
    default_resources = ResourceSpec(cpu="0", memory="0", disk="1Gi")
    categories = ["database", "relational", "embedded"]

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        path = config.get("path", f"/data/{service_name}.db")
        return {
            "SQLITE_PATH": path,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "sql_query",
            "sql_migrate",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        # No network health check for an embedded database.
        return {}

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        # SQLite has no authentication.
        return {}

    def get_k8s_manifests(
        self,
        service_name: str,
        workspace_id: str,
        namespace: str,
        credentials: dict,
        config: dict,
        resources: ResourceSpec,
    ) -> list[dict]:
        # SQLite is embedded — no container or service manifests needed.
        return []
