from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class CassandraService(ServiceDefinition):
    service_type = "cassandra"
    display_name = "Apache Cassandra"
    description = "Distributed wide-column NoSQL database for high availability."
    default_version = "4.1"
    supported_versions = ["3.11", "4.0", "4.1"]
    docker_image_template = "cassandra:{version}"
    default_port = 9042
    default_resources = ResourceSpec(cpu="1", memory="2Gi", disk="10Gi")
    categories = ["database", "nosql", "wide-column"]

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
            "CASSANDRA_HOST": host,
            "CASSANDRA_PORT": port,
            "CASSANDRA_KEYSPACE": credentials.get("keyspace", "pyws_keyspace"),
            "CASSANDRA_USER": credentials["user"],
            "CASSANDRA_PASSWORD": credentials["password"],
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "cql_query",
            "cql_execute",
            "cql_list_keyspaces",
            "cql_describe_table",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {"tcpSocket": {"host": host, "port": self.default_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        keyspace = config.get("keyspace", "pyws_keyspace")
        replication = config.get("replication_factor", 1)
        return [
            (
                f"cqlsh -e \"CREATE KEYSPACE IF NOT EXISTS {keyspace} "
                f"WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': {replication}}};\""
            ),
        ]

    def generate_credentials(self, config: dict) -> dict[str, str]:
        suffix = secrets_mod.token_hex(4)
        return {
            "user": f"pyws_{suffix}",
            "password": secrets_mod.token_urlsafe(24),
            "keyspace": config.get("keyspace", "pyws_keyspace"),
        }
