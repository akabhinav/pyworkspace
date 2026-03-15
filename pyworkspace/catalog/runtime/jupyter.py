from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class JupyterService(ServiceDefinition):
    service_type = "jupyter"
    display_name = "Jupyter Notebook"
    description = "Interactive notebook environment with scipy stack."
    default_version = "latest"
    supported_versions = ["latest"]
    docker_image_template = "jupyter/scipy-notebook:{version}"
    default_port = 8888
    default_resources = ResourceSpec(cpu="1", memory="2Gi", disk="5Gi")
    categories = ["runtime", "notebook"]

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        port = str(self.default_port)
        token = credentials.get("token", "")
        return {
            "JUPYTER_URL": f"http://{host}:{port}",
            "JUPYTER_TOKEN": token,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "jupyter_execute",
            "jupyter_list_kernels",
            "jupyter_create_notebook",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/api/status",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        pip_packages = config.get("pip_packages", [])
        if pip_packages:
            commands.append(f"pip install {' '.join(pip_packages)}")
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "token": secrets_mod.token_urlsafe(32),
        }
