import pytest
from decimal import Decimal

from pyworkspace.billing.metering import ResourceMeter, calculate_cost


class TestCalculateCost:
    def test_zero_usage(self):
        cost = calculate_cost()
        assert cost == Decimal("0.0000")

    def test_cpu_cost(self):
        # 1 core for 1 hour = 3600 core-seconds → $0.05
        cost = calculate_cost(cpu_core_seconds=3600)
        assert cost == Decimal("0.0500")

    def test_memory_cost(self):
        # 1 GiB for 1 hour = 3600 GiB-seconds → $0.01
        cost = calculate_cost(memory_gib_seconds=3600)
        assert cost == Decimal("0.0100")

    def test_disk_cost(self):
        cost = calculate_cost(disk_gib_hours=10)
        assert cost == Decimal("0.0100")

    def test_network_cost(self):
        cost = calculate_cost(network_egress_gb=1)
        assert cost == Decimal("0.1000")

    def test_combined_cost(self):
        cost = calculate_cost(
            cpu_core_seconds=3600,
            memory_gib_seconds=3600,
            disk_gib_hours=10,
            network_egress_gb=1,
        )
        assert cost == Decimal("0.1700")


class TestResourceMeter:
    @pytest.mark.asyncio
    async def test_record_usage_without_k8s(self):
        meter = ResourceMeter(k8s_manager=None)
        usage = await meter.record_usage("ws-1", "org-1")
        assert usage["workspace_id"] == "ws-1"
        assert usage["org_id"] == "org-1"
        assert "cost_usd" in usage
        assert "period_start" in usage
        assert "period_end" in usage
