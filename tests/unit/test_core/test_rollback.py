"""Tests for provisioner rollback on partial failure."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from pyworkspace.core.provisioner import WorkspaceProvisioner, ProvisionError
from pyworkspace.core.specs import ServiceSpec, WorkspaceSpec


class TestProvisionerRollback:
    @pytest.mark.asyncio
    async def test_rollback_deletes_namespace_on_failure(self):
        k8s = AsyncMock()
        # Make health check fail to trigger rollback
        k8s.wait_for_healthy = AsyncMock(side_effect=Exception("pod unhealthy"))
        k8s.create_namespace = AsyncMock()
        k8s.apply_network_policy = AsyncMock()
        k8s.apply_manifest = AsyncMock()
        k8s.delete_namespace = AsyncMock()

        provisioner = WorkspaceProvisioner(k8s_manager=k8s)
        spec = WorkspaceSpec(
            name="rollback-test",
            owner_id="u1",
            org_id="o1",
            tier="standard",
            services=[ServiceSpec(name="pg", type="postgres")],
        )

        workspace = await provisioner.provision(spec)

        with pytest.raises(Exception, match="pod unhealthy"):
            await provisioner.execute_provisioning(workspace, spec)

        # Verify rollback cleaned up namespace
        k8s.delete_namespace.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_removes_secrets(self):
        secrets = AsyncMock()
        secrets.store = AsyncMock()
        secrets.delete = AsyncMock()

        k8s = AsyncMock()
        k8s.wait_for_healthy = AsyncMock(side_effect=Exception("timeout"))
        k8s.create_namespace = AsyncMock()
        k8s.apply_network_policy = AsyncMock()
        k8s.apply_manifest = AsyncMock()
        k8s.delete_namespace = AsyncMock()

        provisioner = WorkspaceProvisioner(k8s_manager=k8s, secret_manager=secrets)
        spec = WorkspaceSpec(
            name="rollback-secrets",
            owner_id="u1",
            org_id="o1",
            tier="standard",
            services=[ServiceSpec(name="pg", type="postgres")],
        )

        workspace = await provisioner.provision(spec)

        with pytest.raises(Exception):
            await provisioner.execute_provisioning(workspace, spec)

        # Secrets were stored then deleted during rollback
        secrets.store.assert_called_once()
        secrets.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_removes_dns(self):
        dns = AsyncMock()
        dns.register = AsyncMock()
        dns.remove = AsyncMock()

        k8s = AsyncMock()
        k8s.wait_for_healthy = AsyncMock(side_effect=Exception("fail"))
        k8s.create_namespace = AsyncMock()
        k8s.apply_network_policy = AsyncMock()
        k8s.apply_manifest = AsyncMock()
        k8s.delete_namespace = AsyncMock()

        provisioner = WorkspaceProvisioner(k8s_manager=k8s, dns_manager=dns)
        spec = WorkspaceSpec(
            name="rollback-dns",
            owner_id="u1",
            org_id="o1",
            tier="standard",
            services=[ServiceSpec(name="pg", type="postgres")],
        )

        workspace = await provisioner.provision(spec)

        with pytest.raises(Exception):
            await provisioner.execute_provisioning(workspace, spec)

        dns.remove.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_continues_on_cleanup_errors(self):
        """Rollback should not raise even if cleanup steps fail."""
        k8s = AsyncMock()
        k8s.wait_for_healthy = AsyncMock(side_effect=Exception("fail"))
        k8s.create_namespace = AsyncMock()
        k8s.apply_network_policy = AsyncMock()
        k8s.apply_manifest = AsyncMock()
        k8s.delete_namespace = AsyncMock(side_effect=Exception("k8s gone"))

        dns = AsyncMock()
        dns.register = AsyncMock()
        dns.remove = AsyncMock(side_effect=Exception("dns gone"))

        provisioner = WorkspaceProvisioner(k8s_manager=k8s, dns_manager=dns)
        spec = WorkspaceSpec(
            name="rollback-errors",
            owner_id="u1",
            org_id="o1",
            tier="standard",
            services=[ServiceSpec(name="pg", type="postgres")],
        )

        workspace = await provisioner.provision(spec)

        # Should still raise the original error, not rollback errors
        with pytest.raises(Exception, match="fail"):
            await provisioner.execute_provisioning(workspace, spec)
