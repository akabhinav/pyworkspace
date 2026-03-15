from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyworkspace.catalog.base import ServiceDefinition

_registry: dict[str, type[ServiceDefinition]] = {}


def register_service(cls: type[ServiceDefinition]) -> type[ServiceDefinition]:
    """Class decorator that registers a ServiceDefinition subclass in the catalog."""
    service_type = cls.service_type
    if not service_type:
        raise ValueError(
            f"{cls.__name__} must define a non-empty 'service_type' class attribute"
        )
    if service_type in _registry:
        raise ValueError(
            f"Service type '{service_type}' is already registered "
            f"by {_registry[service_type].__name__}"
        )
    _registry[service_type] = cls
    return cls


def get_service_definition(service_type: str) -> ServiceDefinition:
    """Instantiate and return a ServiceDefinition for the given service type."""
    if service_type not in _registry:
        available = ", ".join(sorted(_registry)) or "(none)"
        raise KeyError(
            f"Unknown service type '{service_type}'. Available: {available}"
        )
    return _registry[service_type]()


def list_services() -> list[dict]:
    """Return metadata for all registered service definitions."""
    results: list[dict] = []
    for stype, cls in sorted(_registry.items()):
        results.append(
            {
                "type": stype,
                "display_name": cls.display_name,
                "description": cls.description,
                "default_version": cls.default_version,
                "categories": getattr(cls, "categories", []),
                "versions": getattr(cls, "supported_versions", []),
            }
        )
    return results
