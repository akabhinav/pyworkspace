"""Orchestrates full workspace creation — the heart of PyWorkspace."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import structlog

from pyworkspace.catalog import get_service_definition
from pyworkspace.config.constants import (
    PROVISION_STATE_CREATING_NAMESPACE,
    PROVISION_STATE_GENERATING_SECRETS,
    PROVISION_STATE_PROVISIONING_SERVICES,
    PROVISION_STATE_REQUESTED,
    PROVISION_STATE_RESOLVING_SERVICES,
    PROVISION_STATE_RUNNING,
    PROVISION_STATE_STARTING_AGENT,
    PROVISION_STATE_WAITING_HEALTHY,
    SERVICE_STATUS_HEALTHY,
    SERVICE_STATUS_STARTING,
    WORKSPACE_STATUS_ERROR,
    WORKSPACE_STATUS_RUNNING,
)
from pyworkspace.config.settings import get_settings
from pyworkspace.core.resource_quota import validate_quota
from pyworkspace.core.specs import ServiceSpec, WorkspaceSpec

logger = structlog.get_logger()


class ProvisionError(Exception):
    """Raised when workspace provisioning fails."""


class WorkspaceProvisioner:
    """
    Orchestrates workspace creation:
    1. Validate WorkspaceSpec
    2. Create K8s namespace
    3. Apply network policies
    4. Generate credentials for all services
    5. Resolve service dependency graph (topological sort)
    6. Provision services in dependency order (parallel where possible)
    7. Wait for all services healthy
    8. Register DNS entries
    9. Build agent context
    10. Start PyOz agent
    11. Mark workspace RUNNING
    """

    def __init__(
        self,
        k8s_manager=None,
        secret_manager=None,
        dns_manager=None,
        agent_connector=None,
    ) -> None:
        self.k8s = k8s_manager
        self.secrets = secret_manager
        self.dns = dns_manager
        self.agent = agent_connector
        self.settings = get_settings()

    async def provision(self, spec: WorkspaceSpec) -> dict:
        """Create workspace record and kick off provisioning. Returns workspace dict."""
        validate_quota(spec)

        workspace_id = str(uuid.uuid4())
        short_id = workspace_id[:8]
        namespace = f"{self.settings.K8S_WORKSPACE_NAMESPACE_PREFIX}-{short_id}"
        dns_zone = f"{short_id}.{self.settings.WORKSPACE_DNS_DOMAIN}"

        workspace = {
            "id": workspace_id,
            "name": spec.name,
            "owner_id": spec.owner_id,
            "org_id": spec.org_id,
            "tier": spec.tier,
            "status": "provisioning",
            "spec": spec.model_dump(),
            "k8s_namespace": namespace,
            "dns_zone": dns_zone,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "tags": spec.tags,
        }

        logger.info(
            "workspace_provision_started",
            workspace_id=workspace_id,
            name=spec.name,
            services=[s.name for s in spec.services],
        )

        return workspace

    async def execute_provisioning(self, workspace: dict, spec: WorkspaceSpec) -> dict:
        """Run the full provisioning pipeline. Called by Celery task."""
        workspace_id = workspace["id"]
        namespace = workspace["k8s_namespace"]
        dns_zone = workspace["dns_zone"]

        try:
            # Step 1: Create namespace
            logger.info("provision_step", step=PROVISION_STATE_CREATING_NAMESPACE, workspace_id=workspace_id)
            if self.k8s:
                await self.k8s.create_namespace(namespace, workspace_id)
                await self.k8s.apply_network_policy(namespace, workspace_id, spec.egress_allowed)

            # Step 2: Generate secrets
            logger.info("provision_step", step=PROVISION_STATE_GENERATING_SECRETS, workspace_id=workspace_id)
            credentials = {}
            for svc in spec.services:
                defn = get_service_definition(svc.type)
                credentials[svc.name] = defn.generate_credentials(svc.config)
                if self.secrets:
                    await self.secrets.store(workspace_id, svc.name, credentials[svc.name])

            # Step 3: Resolve dependency order
            logger.info("provision_step", step=PROVISION_STATE_RESOLVING_SERVICES, workspace_id=workspace_id)
            layers = _topological_layers(spec.services)

            # Step 4: Provision services layer by layer
            logger.info("provision_step", step=PROVISION_STATE_PROVISIONING_SERVICES, workspace_id=workspace_id)
            provisioned_services = []
            for layer in layers:
                results = await asyncio.gather(
                    *[
                        self._provision_single_service(
                            svc, workspace_id, namespace, dns_zone, credentials[svc.name]
                        )
                        for svc in layer
                    ],
                    return_exceptions=True,
                )
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        raise ProvisionError(
                            f"Failed to provision service '{layer[i].name}': {result}"
                        )
                    provisioned_services.append(result)

            # Step 5: Wait for healthy
            logger.info("provision_step", step=PROVISION_STATE_WAITING_HEALTHY, workspace_id=workspace_id)
            if self.k8s:
                for svc_info in provisioned_services:
                    await self.k8s.wait_for_healthy(
                        namespace, svc_info["service_name"], timeout_seconds=300
                    )

            # Step 6: Start agent
            if spec.agent.enabled:
                logger.info("provision_step", step=PROVISION_STATE_STARTING_AGENT, workspace_id=workspace_id)
                if self.agent:
                    await self.agent.start(
                        workspace_id=workspace_id,
                        namespace=namespace,
                        dns_zone=dns_zone,
                        services=provisioned_services,
                        agent_spec=spec.agent,
                    )

            # Step 7: Mark running
            workspace["status"] = WORKSPACE_STATUS_RUNNING
            workspace["updated_at"] = datetime.now(timezone.utc)
            logger.info(
                "workspace_provisioned",
                workspace_id=workspace_id,
                services_count=len(provisioned_services),
                step=PROVISION_STATE_RUNNING,
            )

            return workspace

        except Exception as e:
            workspace["status"] = WORKSPACE_STATUS_ERROR
            workspace["error_message"] = str(e)
            workspace["updated_at"] = datetime.now(timezone.utc)
            logger.error("workspace_provision_failed", workspace_id=workspace_id, error=str(e))
            raise

    async def _provision_single_service(
        self,
        service_spec: ServiceSpec,
        workspace_id: str,
        namespace: str,
        dns_zone: str,
        credentials: dict,
    ) -> dict:
        """Provision a single service: create K8s resources, register DNS."""
        defn = get_service_definition(service_spec.type)
        resources = service_spec.resources or defn.default_resources

        # Generate K8s manifests
        manifests = defn.get_k8s_manifests(
            service_name=service_spec.name,
            workspace_id=workspace_id,
            namespace=namespace,
            credentials=credentials,
            config=service_spec.config,
            resources=resources,
        )

        # Apply manifests
        if self.k8s:
            for manifest in manifests:
                await self.k8s.apply_manifest(manifest)

        # Register DNS
        internal_dns = f"{service_spec.name}.{dns_zone}"
        if self.dns:
            await self.dns.register(dns_zone, service_spec.name, internal_dns)

        # Get env vars for cross-service wiring
        env_vars = defn.get_env_vars(service_spec.name, dns_zone, credentials, service_spec.config)

        service_info = {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "service_name": service_spec.name,
            "service_type": service_spec.type,
            "status": SERVICE_STATUS_STARTING,
            "internal_dns": internal_dns,
            "internal_port": defn.default_port,
            "env_vars": env_vars,
            "agent_tools": defn.get_agent_tools(),
            "credentials": credentials,
        }

        logger.info(
            "service_provisioned",
            workspace_id=workspace_id,
            service=service_spec.name,
            type=service_spec.type,
        )

        return service_info


def _build_dependency_graph(services: list[ServiceSpec]) -> dict[str, list[str]]:
    """Build adjacency list from depends_on."""
    graph: dict[str, list[str]] = {svc.name: list(svc.depends_on) for svc in services}
    return graph


def _topological_layers(services: list[ServiceSpec]) -> list[list[ServiceSpec]]:
    """
    Returns services grouped into layers for parallel provisioning.
    Layer 0: no dependencies. Layer 1: depends only on layer 0. Etc.
    """
    by_name = {svc.name: svc for svc in services}
    graph = _build_dependency_graph(services)
    in_degree: dict[str, int] = {name: len(deps) for name, deps in graph.items()}
    resolved: set[str] = set()
    layers: list[list[ServiceSpec]] = []

    remaining = set(by_name.keys())
    while remaining:
        # Find all services with no unresolved dependencies
        layer_names = [
            name for name in remaining if all(dep in resolved for dep in graph[name])
        ]
        if not layer_names:
            raise ProvisionError(
                f"Circular dependency detected among: {remaining}"
            )
        layers.append([by_name[name] for name in layer_names])
        resolved.update(layer_names)
        remaining -= set(layer_names)

    return layers
