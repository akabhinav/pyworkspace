from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class CodeExecutorService(ServiceDefinition):
    service_type = "code_executor"
    display_name = "Code Executor"
    description = "Sandboxed multi-language code execution service."
    default_version = "latest"
    supported_versions = ["latest"]
    docker_image_template = "pyworkspace/code-executor:{version}"
    default_port = 8080
    default_resources = ResourceSpec(cpu="1", memory="2Gi", disk="5Gi")
    categories = ["runtime"]

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
            "CODE_EXECUTOR_URL": f"http://{host}:{port}",
            "CODE_EXECUTOR_TOKEN": credentials.get("token", ""),
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "execute_python",
            "execute_node",
            "execute_java",
            "execute_shell",
            "install_pip",
            "install_npm",
            "run_tests",
            "run_build",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/health",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        pip_packages = config.get("pip_packages", [])
        if pip_packages:
            commands.append(f"pip install {' '.join(pip_packages)}")
        npm_packages = config.get("npm_packages", [])
        if npm_packages:
            commands.append(f"npm install -g {' '.join(npm_packages)}")
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "token": secrets_mod.token_urlsafe(32),
        }
