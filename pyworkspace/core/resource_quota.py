"""Resource quota enforcement per workspace tier."""

from __future__ import annotations

from pyworkspace.config.constants import TIER_LIMITS
from pyworkspace.core.specs import ResourceSpec, WorkspaceSpec


class QuotaExceededError(Exception):
    """Raised when a workspace spec exceeds its tier limits."""


def _parse_memory_gi(value: str) -> float:
    """Parse memory string like '8Gi' or '512Mi' to GiB."""
    v = value.strip()
    if v.endswith("Gi"):
        return float(v[:-2])
    if v.endswith("Mi"):
        return float(v[:-2]) / 1024
    return float(v)


def _parse_cpu(value: str) -> float:
    """Parse CPU string like '4' or '500m' to cores."""
    v = value.strip()
    if v.endswith("m"):
        return float(v[:-1]) / 1000
    return float(v)


def validate_quota(spec: WorkspaceSpec) -> None:
    """Validate that a workspace spec fits within its tier limits."""
    limits = TIER_LIMITS.get(spec.tier)
    if limits is None:
        raise QuotaExceededError(f"Unknown tier: {spec.tier}")

    max_services = int(limits["max_services"])
    if len(spec.services) > max_services:
        raise QuotaExceededError(
            f"Tier '{spec.tier}' allows max {max_services} services, "
            f"got {len(spec.services)}"
        )

    total_cpu = _parse_cpu(spec.resources.cpu)
    max_cpu = int(limits["cpu"])
    if total_cpu > max_cpu:
        raise QuotaExceededError(
            f"Tier '{spec.tier}' allows max {max_cpu} CPU cores, requested {total_cpu}"
        )

    total_mem = _parse_memory_gi(spec.resources.memory)
    max_mem = int(limits["memory_gi"])
    if total_mem > max_mem:
        raise QuotaExceededError(
            f"Tier '{spec.tier}' allows max {max_mem}Gi memory, requested {total_mem}Gi"
        )


def calculate_service_resources(
    spec: WorkspaceSpec,
) -> dict[str, ResourceSpec]:
    """Return effective ResourceSpec per service, falling back to defaults."""
    from pyworkspace.catalog import get_service_definition

    result: dict[str, ResourceSpec] = {}
    for svc in spec.services:
        if svc.resources:
            result[svc.name] = svc.resources
        else:
            defn = get_service_definition(svc.type)
            result[svc.name] = defn.default_resources
    return result
