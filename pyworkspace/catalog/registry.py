from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from pyworkspace.catalog.base import ServiceDefinition

logger = structlog.get_logger()

# Compile-time registry: service_type → ServiceDefinition class
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
    """Instantiate and return a ServiceDefinition for the given service type.

    Checks compile-time registry first, then falls back to plugin registry
    for services provided by external plugins.
    """
    # 1. Check compile-time registry (built-in services)
    if service_type in _registry:
        return _registry[service_type]()

    # 2. Check plugin registry (external services registered at runtime)
    try:
        from pyworkspace.plugins.registry import plugin_registry
        if plugin_registry.has_plugin(service_type):
            manifest = plugin_registry.get(service_type)
            if manifest.service is not None:
                from pyworkspace.catalog.plugin_adapter import PluginServiceAdapter
                return PluginServiceAdapter(manifest)
    except ImportError:
        pass

    available = ", ".join(sorted(_all_service_types())) or "(none)"
    raise KeyError(
        f"Unknown service type '{service_type}'. Available: {available}"
    )


def list_services() -> list[dict]:
    """Return metadata for all registered service definitions (built-in + plugins)."""
    results: list[dict] = []

    # Built-in services
    for stype, cls in sorted(_registry.items()):
        results.append(
            {
                "type": stype,
                "display_name": cls.display_name,
                "description": cls.description,
                "default_version": cls.default_version,
                "categories": getattr(cls, "categories", []),
                "versions": getattr(cls, "supported_versions", []),
                "source": "builtin",
            }
        )

    # Plugin-provided services
    try:
        from pyworkspace.plugins.registry import plugin_registry
        for manifest in plugin_registry.get_plugins_with_service():
            if manifest.name not in _registry:  # avoid duplicates
                results.append(
                    {
                        "type": manifest.name,
                        "display_name": manifest.display_name or manifest.name,
                        "description": manifest.description,
                        "default_version": manifest.version,
                        "categories": manifest.categories,
                        "versions": [manifest.version],
                        "source": "plugin",
                        "team": manifest.team,
                    }
                )
    except ImportError:
        pass

    return results


def _all_service_types() -> set[str]:
    """Get all known service types from both registries."""
    types = set(_registry.keys())
    try:
        from pyworkspace.plugins.registry import plugin_registry
        for m in plugin_registry.get_plugins_with_service():
            types.add(m.name)
    except ImportError:
        pass
    return types
