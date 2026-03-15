"""PyOz agent workspace bootstrap — connects agent to all workspace services."""
from __future__ import annotations
import structlog
from pyworkspace.config.settings import get_settings
from pyworkspace.core.specs import AgentSpec

logger = structlog.get_logger()

class AgentConnector:
    """Bootstraps the PyOz agent in a workspace with full service access."""

    def __init__(self, k8s_manager=None):
        self.k8s = k8s_manager
        self.settings = get_settings()

    async def start(
        self,
        workspace_id: str,
        namespace: str,
        dns_zone: str,
        services: list[dict],
        agent_spec: AgentSpec,
    ) -> dict:
        """Start PyOz agent pod with workspace context."""
        from pyworkspace.agent.context_builder import ContextBuilder

        context = ContextBuilder.build(
            workspace_id=workspace_id,
            workspace_name=namespace,
            dns_zone=dns_zone,
            services=services,
        )

        image = agent_spec.image or self.settings.PYOZ_IMAGE
        resources = agent_spec.resources
        cpu = resources.cpu if resources else self.settings.PYOZ_CPU
        memory = resources.memory if resources else self.settings.PYOZ_MEMORY

        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "pyoz-agent",
                "namespace": namespace,
                "labels": {"app": "pyoz-agent", "workspace": workspace_id},
            },
            "spec": {
                "serviceAccountName": "workspace-agent",
                "securityContext": {
                    "runAsUser": 1000,
                    "runAsGroup": 1000,
                    "fsGroup": 1000,
                },
                "containers": [{
                    "name": "pyoz-agent",
                    "image": image,
                    "env": [
                        {"name": k, "value": str(v)}
                        for k, v in context.environment.items()
                    ] + [
                        {"name": "WORKSPACE_ID", "value": workspace_id},
                        {"name": "WORKSPACE_ROOT", "value": context.workspace_root},
                        {"name": "DNS_ZONE", "value": dns_zone},
                    ],
                    "resources": {
                        "requests": {"cpu": cpu, "memory": memory},
                        "limits": {"cpu": cpu, "memory": memory},
                    },
                    "volumeMounts": [
                        {"name": "workspace", "mountPath": "/workspace"},
                    ],
                    "securityContext": {
                        "readOnlyRootFilesystem": True,
                        "allowPrivilegeEscalation": False,
                    },
                }],
                "volumes": [
                    {"name": "workspace", "emptyDir": {}},
                ],
            },
        }

        if self.k8s:
            await self.k8s.apply_manifest(pod_manifest)

        logger.info("agent_started", workspace_id=workspace_id, image=image)

        return {
            "workspace_id": workspace_id,
            "pod_name": "pyoz-agent",
            "image": image,
            "status": "starting",
            "system_prompt": context.services_summary,
        }

    async def stop(self, workspace_id: str, namespace: str) -> None:
        logger.info("agent_stopped", workspace_id=workspace_id)

    async def restart(self, workspace_id: str, namespace: str, services: list[dict], agent_spec: AgentSpec, dns_zone: str) -> dict:
        await self.stop(workspace_id, namespace)
        return await self.start(workspace_id, namespace, dns_zone, services, agent_spec)
