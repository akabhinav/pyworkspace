"""Tests for resource quota validation."""
import pytest
from pyworkspace.core.resource_quota import validate_quota, QuotaExceededError
from pyworkspace.core.specs import WorkspaceSpec, ServiceSpec, ResourceSpec

class TestResourceQuota:
    def test_valid_dev_tier(self):
        spec = WorkspaceSpec(
            name="test", owner_id="u", org_id="o", tier="dev",
            services=[ServiceSpec(name="pg", type="postgres")],
            resources=ResourceSpec(cpu="2", memory="4Gi"),
        )
        validate_quota(spec)  # Should not raise

    def test_dev_tier_service_limit(self):
        spec = WorkspaceSpec(
            name="test", owner_id="u", org_id="o", tier="dev",
            services=[ServiceSpec(name=f"s{i}", type="redis") for i in range(6)],
        )
        with pytest.raises(QuotaExceededError, match="max 5 services"):
            validate_quota(spec)

    def test_dev_tier_cpu_limit(self):
        spec = WorkspaceSpec(
            name="test", owner_id="u", org_id="o", tier="dev",
            resources=ResourceSpec(cpu="8", memory="4Gi"),
        )
        with pytest.raises(QuotaExceededError, match="CPU"):
            validate_quota(spec)

    def test_enterprise_tier_large_spec(self):
        spec = WorkspaceSpec(
            name="test", owner_id="u", org_id="o", tier="enterprise",
            services=[ServiceSpec(name=f"s{i}", type="redis") for i in range(20)],
            resources=ResourceSpec(cpu="32", memory="64Gi"),
        )
        validate_quota(spec)  # Should not raise
