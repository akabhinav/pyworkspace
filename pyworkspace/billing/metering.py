"""Resource usage tracking — CPU/RAM/disk/time metering."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import structlog

logger = structlog.get_logger()

# Cost rates per unit per hour (USD)
_COST_RATES = {
    "cpu_core_hour": Decimal("0.05"),
    "memory_gib_hour": Decimal("0.01"),
    "disk_gib_hour": Decimal("0.001"),
    "network_egress_gb": Decimal("0.10"),
}


class ResourceMeter:
    """Runs periodically to record resource usage per workspace."""

    def __init__(self, k8s_manager=None) -> None:
        self.k8s = k8s_manager

    async def record_usage(self, workspace_id: str, org_id: str) -> dict:
        """Record current resource usage for a workspace."""
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(seconds=60)

        # In production: query K8s metrics-server
        metrics = {"cpu_cores": 0.0, "memory_gib": 0.0, "disk_gib": 0.0}
        if self.k8s:
            metrics = await self.k8s.get_namespace_resource_metrics(f"pyws-{workspace_id[:8]}")

        cpu_seconds = metrics.get("cpu_cores", 0.0) * 60
        mem_seconds = metrics.get("memory_gib", 0.0) * 60
        disk_hours = metrics.get("disk_gib", 0.0) / 60

        cost = calculate_cost(
            cpu_core_seconds=cpu_seconds,
            memory_gib_seconds=mem_seconds,
            disk_gib_hours=disk_hours,
        )

        usage = {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "org_id": org_id,
            "period_start": period_start.isoformat(),
            "period_end": now.isoformat(),
            "cpu_core_seconds": cpu_seconds,
            "memory_gib_seconds": mem_seconds,
            "disk_gib_hours": disk_hours,
            "network_egress_gb": 0.0,
            "cost_usd": str(cost),
        }

        logger.debug("usage_recorded", workspace_id=workspace_id, cost_usd=str(cost))
        return usage


def calculate_cost(
    cpu_core_seconds: float = 0,
    memory_gib_seconds: float = 0,
    disk_gib_hours: float = 0,
    network_egress_gb: float = 0,
) -> Decimal:
    """Calculate cost in USD from resource usage."""
    cpu_hours = Decimal(str(cpu_core_seconds)) / Decimal("3600")
    mem_hours = Decimal(str(memory_gib_seconds)) / Decimal("3600")

    cost = (
        cpu_hours * _COST_RATES["cpu_core_hour"]
        + mem_hours * _COST_RATES["memory_gib_hour"]
        + Decimal(str(disk_gib_hours)) * _COST_RATES["disk_gib_hour"]
        + Decimal(str(network_egress_gb)) * _COST_RATES["network_egress_gb"]
    )
    return cost.quantize(Decimal("0.0001"))
