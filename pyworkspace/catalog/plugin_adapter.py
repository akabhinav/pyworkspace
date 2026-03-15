"""Adapter that wraps a PluginManifest as a ServiceDefinition.

This lets plugin-provided services (PySandbox, PyTrace, etc.) work with
the existing provisioner without the provisioner knowing about plugins.
The plugin team defines their service in a manifest — this adapter translates
it into the ServiceDefinition interface that the provisioner already uses.
"""

from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.core.specs import ResourceSpec
from pyworkspace.plugins.manifest import PluginManifest


class PluginServiceAdapter(ServiceDefinition):
    """Adapts a PluginManifest into a ServiceDefinition for the provisioner."""

    def __init__(self, manifest: PluginManifest) -> None:
        self._manifest = manifest
        svc = manifest.service  # guaranteed non-None by caller

        self.service_type = manifest.name
        self.display_name = manifest.display_name or manifest.name
        self.description = manifest.description
        self.default_version = manifest.version
        self.supported_versions = [manifest.version]
        self.docker_image_template = svc.image if svc else ""
        self.default_port = svc.port if svc else 0
        self.default_resources = ResourceSpec(
            cpu=svc.resources.cpu if svc else "0.5",
            memory=svc.resources.memory if svc else "512Mi",
            disk=svc.resources.disk if svc else "1Gi",
        )
        self.categories = manifest.categories

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        """Build env vars from the plugin's manifest config + standard patterns."""
        prefix = service_name.upper().replace("-", "_")
        host = f"{service_name}.{workspace_dns_zone}"
        env = {
            f"{prefix}_HOST": host,
            f"{prefix}_PORT": str(self.default_port),
            f"{prefix}_URL": f"http://{host}:{self.default_port}",
        }
        # Include any static env vars from the manifest
        if self._manifest.service:
            env.update(self._manifest.service.env)
        return env

    def get_agent_tools(self) -> list[str]:
        """Return tool names from the plugin manifest."""
        return self._manifest.tool_names

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        svc = self._manifest.service
        if svc and svc.health_check:
            return {
                "httpGet": {
                    "path": svc.health_check.endpoint,
                    "port": svc.port,
                },
                "periodSeconds": svc.health_check.interval_seconds,
                "timeoutSeconds": svc.health_check.timeout_seconds,
            }
        return {"tcpSocket": {"port": self.default_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        return []

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "api_key": secrets_mod.token_urlsafe(32),
        }

    def get_docker_image(self, version: str | None = None) -> str:
        """Plugin images don't use templates — return the manifest image directly."""
        return self._manifest.service.image if self._manifest.service else ""

    def get_k8s_manifests(
        self,
        service_name: str,
        workspace_id: str,
        namespace: str,
        credentials: dict,
        config: dict,
        resources: ResourceSpec,
    ) -> list[dict]:
        """Generate K8s manifests using plugin's service spec."""
        svc = self._manifest.service
        if not svc:
            return []

        # Use plugin's security context
        container_security = svc.security_context

        # Merge env vars: manifest static + credentials
        env_list = [{"name": k, "value": v} for k, v in svc.env.items()]
        for k, v in credentials.items():
            env_list.append({"name": k.upper(), "value": str(v)})

        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": service_name,
                "namespace": namespace,
                "labels": {
                    "app": service_name,
                    "workspace": workspace_id,
                    "plugin": self._manifest.name,
                },
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": service_name}},
                "template": {
                    "metadata": {
                        "labels": {
                            "app": service_name,
                            "workspace": workspace_id,
                            "plugin": self._manifest.name,
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": service_name,
                                "image": svc.image,
                                "ports": [{"containerPort": svc.port}],
                                "env": env_list,
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
                                "securityContext": container_security,
                            }
                        ],
                    },
                },
            },
        }

        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": service_name, "namespace": namespace},
            "spec": {
                "selector": {"app": service_name},
                "ports": [{"port": svc.port, "targetPort": svc.port}],
            },
        }

        return [deployment, service]
