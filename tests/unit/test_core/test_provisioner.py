"""Tests for workspace provisioner."""
import pytest
from pyworkspace.core.provisioner import WorkspaceProvisioner, _topological_layers
from pyworkspace.core.specs import ServiceSpec, WorkspaceSpec

class TestTopologicalLayers:
    def test_no_dependencies(self):
        services = [
            ServiceSpec(name="postgres", type="postgres"),
            ServiceSpec(name="redis", type="redis"),
        ]
        layers = _topological_layers(services)
        assert len(layers) == 1
        assert len(layers[0]) == 2

    def test_simple_dependency(self):
        services = [
            ServiceSpec(name="prometheus", type="prometheus"),
            ServiceSpec(name="grafana", type="grafana", depends_on=["prometheus"]),
        ]
        layers = _topological_layers(services)
        assert len(layers) == 2
        assert layers[0][0].name == "prometheus"
        assert layers[1][0].name == "grafana"

    def test_complex_dependencies(self):
        services = [
            ServiceSpec(name="postgres", type="postgres"),
            ServiceSpec(name="redis", type="redis"),
            ServiceSpec(name="kafka", type="kafka"),
            ServiceSpec(name="app", type="code_executor", depends_on=["postgres", "redis", "kafka"]),
        ]
        layers = _topological_layers(services)
        assert len(layers) == 2
        assert len(layers[0]) == 3  # postgres, redis, kafka in parallel
        assert layers[1][0].name == "app"

    def test_circular_dependency_raises(self):
        from pyworkspace.core.provisioner import ProvisionError
        services = [
            ServiceSpec(name="a", type="postgres", depends_on=["b"]),
            ServiceSpec(name="b", type="redis", depends_on=["a"]),
        ]
        with pytest.raises(ProvisionError, match="Circular"):
            _topological_layers(services)

class TestWorkspaceProvisioner:
    @pytest.mark.asyncio
    async def test_provision_creates_workspace(self, sample_workspace_spec):
        provisioner = WorkspaceProvisioner()
        result = await provisioner.provision(sample_workspace_spec)
        assert result["name"] == "test-workspace"
        assert result["status"] == "provisioning"
        assert result["k8s_namespace"].startswith("pyws-")
        assert "id" in result

    @pytest.mark.asyncio
    async def test_provision_validates_quota(self):
        from pyworkspace.core.resource_quota import QuotaExceededError
        spec = WorkspaceSpec(
            name="test",
            owner_id="u",
            org_id="o",
            tier="dev",
            services=[ServiceSpec(name=f"svc{i}", type="redis") for i in range(10)],
        )
        provisioner = WorkspaceProvisioner()
        with pytest.raises(QuotaExceededError):
            await provisioner.provision(spec)
