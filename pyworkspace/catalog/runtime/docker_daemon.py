from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class DockerDaemonService(ServiceDefinition):
    service_type = "docker_daemon"
    display_name = "Docker-in-Docker"
    description = "Docker daemon (DinD) for building and running containers inside a workspace."
    default_version = "latest"
    supported_versions = ["latest", "24-dind", "25-dind"]
    docker_image_template = "docker:{version}"
    default_port = 2375
    default_resources = ResourceSpec(cpu="1", memory="2Gi", disk="20Gi")
    categories = ["runtime", "docker"]

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
            "DOCKER_HOST": f"tcp://{host}:{port}",
            "DOCKER_TLS_CERTDIR": "",
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "docker_build",
            "docker_run",
            "docker_ps",
            "docker_logs",
            "docker_stop",
            "docker_rm",
            "docker_images",
            "docker_pull",
            "docker_push",
            "docker_exec",
            "docker_compose_up",
            "docker_compose_down",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/_ping",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {}
