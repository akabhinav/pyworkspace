from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class RabbitMQService(ServiceDefinition):
    service_type = "rabbitmq"
    display_name = "RabbitMQ"
    description = "Message broker with management UI, supporting AMQP, MQTT, and STOMP."
    default_version = "3.12"
    supported_versions = ["3.11", "3.12", "3.13"]
    docker_image_template = "rabbitmq:{version}-management"
    default_port = 5672
    default_resources = ResourceSpec(cpu="0.5", memory="512Mi", disk="2Gi")
    categories = ["messaging"]

    _management_port = 15672

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
        return {
            "RABBITMQ_URL": f"amqp://{user}:{password}@{host}:{port}/",
            "RABBITMQ_HOST": host,
            "RABBITMQ_PORT": port,
            "RABBITMQ_MANAGEMENT_URL": f"http://{host}:{self._management_port}",
            "RABBITMQ_USER": user,
            "RABBITMQ_PASSWORD": password,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "rabbitmq_publish",
            "rabbitmq_consume",
            "rabbitmq_list_queues",
            "rabbitmq_create_queue",
            "rabbitmq_list_exchanges",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self._management_port,
                "path": "/api/health/checks/alarms",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        vhosts = config.get("vhosts", [])
        for vhost in vhosts:
            commands.append(f"rabbitmqctl add_vhost {vhost}")
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        suffix = secrets_mod.token_hex(4)
        return {
            "user": f"pyws_{suffix}",
            "password": secrets_mod.token_urlsafe(24),
        }
