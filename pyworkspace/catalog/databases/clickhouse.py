from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class ClickHouseService(ServiceDefinition):
    service_type = "clickhouse"
    display_name = "ClickHouse"
    description = "Column-oriented OLAP database for real-time analytics."
    default_version = "23.8"
    supported_versions = ["22.8", "23.3", "23.8"]
    docker_image_template = "clickhouse/clickhouse-server:{version}"
    default_port = 8123
    default_resources = ResourceSpec(cpu="1", memory="2Gi", disk="10Gi")
    categories = ["database", "analytics", "columnar"]

    _native_port = 9000

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        http_port = str(self.default_port)
        native_port = str(self._native_port)
        database = credentials.get("database", "pyws_db")
        return {
            "CLICKHOUSE_URL": f"http://{host}:{http_port}",
            "CLICKHOUSE_HOST": host,
            "CLICKHOUSE_HTTP_PORT": http_port,
            "CLICKHOUSE_NATIVE_PORT": native_port,
            "CLICKHOUSE_DB": database,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "sql_query",
            "db_list_tables",
            "db_describe_table",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/ping",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        database = config.get("database", "pyws_db")
        return [
            f'clickhouse-client --query "CREATE DATABASE IF NOT EXISTS {database}"',
        ]

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "user": "default",
            "password": secrets_mod.token_urlsafe(24),
            "database": config.get("database", "pyws_db"),
        }
