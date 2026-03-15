from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class MySQLService(ServiceDefinition):
    service_type = "mysql"
    display_name = "MySQL"
    description = "Popular open-source relational database."
    default_version = "8.0"
    supported_versions = ["5.7", "8.0", "8.1", "8.2"]
    docker_image_template = "mysql:{version}"
    default_port = 3306
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
        root_password = credentials["root_password"]
        return {
            "MYSQL_URL": f"mysql://{user}:{password}@{host}:{port}/{database}",
            "MYSQL_HOST": host,
            "MYSQL_PORT": port,
            "MYSQL_DB": database,
            "MYSQL_USER": user,
            "MYSQL_PASSWORD": password,
            "MYSQL_ROOT_PASSWORD": root_password,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "sql_query",
            "sql_migrate",
            "db_list_tables",
            "db_describe_table",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {"tcpSocket": {"host": host, "port": self.default_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        charset = config.get("charset", "utf8mb4")
        commands.append(
            f'mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e '
            f'"ALTER DATABASE $MYSQL_DB CHARACTER SET {charset} COLLATE {charset}_unicode_ci;"'
        )
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        suffix = secrets_mod.token_hex(4)
        return {
            "user": f"pyws_{suffix}",
            "password": secrets_mod.token_urlsafe(24),
            "root_password": secrets_mod.token_urlsafe(32),
            "database": config.get("database", "pyws_db"),
        }
