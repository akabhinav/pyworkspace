from __future__ import annotations

import secrets as secrets_mod
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pyworkspace.core.specs import ResourceSpec


@dataclass
class ServiceConnection:
    host: str
    port: int
    env_vars: dict[str, str]
    agent_tools: list[str]
    health_endpoint: str | None = None
    credentials: dict[str, str] = field(default_factory=dict)


class ServiceDefinition(ABC):
    service_type: str = ""
    display_name: str = ""
    description: str = ""
    default_version: str = "latest"
    supported_versions: list[str] = []
    docker_image_template: str = ""
    default_port: int = 0
    default_resources: ResourceSpec = ResourceSpec()
    categories: list[str] = []

    @abstractmethod
    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]: ...

    @abstractmethod
    def get_agent_tools(self) -> list[str]: ...

    @abstractmethod
    def get_health_check(
        self, service_name: str, workspace_dns_zone: str
    ) -> dict: ...

    @abstractmethod
    def get_init_commands(self, config: dict) -> list[str]: ...

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "user": config.get("user", "pyws_user"),
            "password": secrets_mod.token_urlsafe(24),
            "database": config.get("db", "pyws_db"),
        }

    def get_docker_image(self, version: str | None = None) -> str:
        v = version or self.default_version
        return self.docker_image_template.format(version=v)

    def get_k8s_manifests(
        self,
        service_name: str,
        workspace_id: str,
        namespace: str,
        credentials: dict,
        config: dict,
        resources: ResourceSpec,
    ) -> list[dict]:
        image = self.get_docker_image(config.get("version"))
        env_vars: dict[str, str] = {}
        # merge credential env vars
        for k, v in credentials.items():
            env_vars[k.upper()] = str(v)

        # Deployment
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": service_name,
                "namespace": namespace,
                "labels": {"app": service_name, "workspace": workspace_id},
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": service_name}},
                "template": {
                    "metadata": {
                        "labels": {
                            "app": service_name,
                            "workspace": workspace_id,
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": service_name,
                                "image": image,
                                "ports": [
                                    {"containerPort": self.default_port}
                                ],
                                "env": [
                                    {"name": k, "value": v}
                                    for k, v in env_vars.items()
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": resources.cpu,
                                        "memory": resources.memory,
                                    },
                                    "limits": {
                                        "cpu": resources.cpu,
                                        "memory": resources.memory,
                                    },
                                },
                            }
                        ],
                    },
                },
            },
        }

        # Service
        svc = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": service_name, "namespace": namespace},
            "spec": {
                "selector": {"app": service_name},
                "ports": [
                    {
                        "port": self.default_port,
                        "targetPort": self.default_port,
                    }
                ],
            },
        }

        manifests = [deployment, svc]

        # PVC if persistent
        pvc = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": f"{service_name}-data",
                "namespace": namespace,
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": resources.disk}},
            },
        }
        manifests.append(pvc)

        return manifests
