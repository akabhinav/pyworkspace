from __future__ import annotations

import secrets as secrets_mod
from typing import Any

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class PostgresService(ServiceDefinition):
    service_type = "postgres"
    display_name = "PostgreSQL"
    description = "Relational database with advanced SQL support, JSONB, and extensions."
    default_version = "16"
    supported_versions = ["12", "13", "14", "15", "16"]
    docker_image_template = "postgres:{version}"
    default_port = 5432
    default_resources = ResourceSpec(cpu="0.5", memory="512Mi", disk="5Gi")
    categories = ["database", "relational"]

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        port = str(self.default_port)
        user = credentials["user"]
        password = credentials["password"]
        database = credentials["database"]
        return {
            "POSTGRES_URL": f"postgresql://{user}:{password}@{host}:{port}/{database}",
            "POSTGRES_HOST": host,
            "POSTGRES_PORT": port,
            "POSTGRES_DB": database,
            "POSTGRES_USER": user,
            "POSTGRES_PASSWORD": password,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "sql_query",
            "sql_migrate",
            "sql_explain",
            "db_list_tables",
            "db_describe_table",
            "db_list_indexes",
            "db_vacuum",
            "db_dump",
            "db_restore",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {"tcpSocket": {"host": host, "port": self.default_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        extensions = config.get("extensions", [])
        for ext in extensions:
            commands.append(f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS {ext};"')
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        suffix = secrets_mod.token_hex(4)
        return {
            "user": f"pyws_{suffix}",
            "password": secrets_mod.token_urlsafe(24),
            "database": config.get("db", config.get("database", "pyws_db")),
        }
