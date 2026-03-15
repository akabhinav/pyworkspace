"""Resolve service dependencies and build provision order."""

from __future__ import annotations

from pyworkspace.core.specs import ServiceSpec


class DependencyResolutionError(Exception):
    """Raised when service dependencies cannot be resolved."""


def resolve_dependencies(services: list[ServiceSpec]) -> list[list[ServiceSpec]]:
    """
    Resolve service dependencies into ordered layers for parallel provisioning.
    Returns list of layers — each layer can be provisioned in parallel.
    """
    by_name = {svc.name: svc for svc in services}

    # Validate all depends_on references exist
    for svc in services:
        for dep in svc.depends_on:
            if dep not in by_name:
                raise DependencyResolutionError(
                    f"Service '{svc.name}' depends on '{dep}' which is not defined"
                )

    resolved: set[str] = set()
    layers: list[list[ServiceSpec]] = []
    remaining = set(by_name.keys())

    while remaining:
        layer_names = [
            name
            for name in remaining
            if all(dep in resolved for dep in by_name[name].depends_on)
        ]

        if not layer_names:
            raise DependencyResolutionError(
                f"Circular dependency detected among: {remaining}"
            )

        layers.append([by_name[name] for name in sorted(layer_names)])
        resolved.update(layer_names)
        remaining -= set(layer_names)

    return layers


def validate_no_cycles(services: list[ServiceSpec]) -> bool:
    """Check for circular dependencies. Returns True if no cycles."""
    try:
        resolve_dependencies(services)
        return True
    except DependencyResolutionError:
        return False
