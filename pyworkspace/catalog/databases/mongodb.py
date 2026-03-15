from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class MongoDBService(ServiceDefinition):
    service_type = "mongodb"
    display_name = "MongoDB"
    description = "Document-oriented NoSQL database."
    default_version = "7"
    supported_versions = ["5", "6", "7"]
    docker_image_template = "mongo:{version}"
    default_port = 27017
    default_resources = ResourceSpec(cpu="0.5", memory="512Mi", disk="5Gi")
    categories = ["database", "nosql", "document"]

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
            "MONGODB_URI": f"mongodb://{user}:{password}@{host}:{port}/{database}?authSource=admin",
            "MONGODB_HOST": host,
            "MONGODB_PORT": port,
            "MONGODB_DB": database,
            "MONGODB_USER": user,
            "MONGODB_PASSWORD": password,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "mongo_query",
            "mongo_insert",
            "mongo_update",
            "mongo_delete",
            "mongo_list_collections",
            "mongo_aggregate",
            "mongo_create_index",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {"tcpSocket": {"host": host, "port": self.default_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        collections = config.get("collections", [])
        for coll in collections:
            commands.append(
                f'mongosh "$MONGODB_URI" --eval "db.createCollection(\'{coll}\')"'
            )
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        suffix = secrets_mod.token_hex(4)
        return {
            "user": f"pyws_{suffix}",
            "password": secrets_mod.token_urlsafe(24),
            "database": config.get("database", "pyws_db"),
        }
