"""Runtime plugin registry — discovers and manages external component manifests.

Unlike the compile-time @register_service catalog, this registry loads plugins
at runtime via manifest files, HTTP discovery, or API registration. Teams can
deploy and register independently without touching PyWorkspace code.
"""

from __future__ import annotations

import structlog
from typing import Any

from pyworkspace.plugins.manifest import PluginManifest, PluginToolSpec

logger = structlog.get_logger()


class PluginNotFoundError(Exception):
    pass


class PluginRegistry:
    """Central registry for all discovered plugins.

    Thread-safe for reads (dict lookups). Write operations (register/unregister)
    should happen during startup or via the admin API.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PluginManifest] = {}
        self._tool_index: dict[str, tuple[str, PluginToolSpec]] = {}  # tool_name → (plugin_name, spec)

    def register(self, manifest: PluginManifest) -> None:
        """Register a plugin from its manifest."""
        name = manifest.name

        if name in self._plugins:
            old_version = self._plugins[name].version
            logger.info(
                "plugin_updated",
                plugin=name,
                old_version=old_version,
                new_version=manifest.version,
            )
            # Remove old tool index entries
            self._remove_tool_index(name)

        self._plugins[name] = manifest

        # Index tools for fast lookup
        for tool in manifest.tools:
            if tool.name in self._tool_index:
                existing_plugin = self._tool_index[tool.name][0]
                logger.warning(
                    "tool_name_collision",
                    tool=tool.name,
                    existing_plugin=existing_plugin,
                    new_plugin=name,
                )
            self._tool_index[tool.name] = (name, tool)

        logger.info(
            "plugin_registered",
            plugin=name,
            version=manifest.version,
            tools=manifest.tool_names,
            events_pub=manifest.events.publishes,
            events_sub=manifest.events.subscribes,
        )

    def unregister(self, name: str) -> None:
        """Remove a plugin from the registry."""
        if name not in self._plugins:
            raise PluginNotFoundError(f"Plugin '{name}' not found")
        self._remove_tool_index(name)
        del self._plugins[name]
        logger.info("plugin_unregistered", plugin=name)

    def get(self, name: str) -> PluginManifest:
        """Get a plugin manifest by name."""
        if name not in self._plugins:
            available = ", ".join(sorted(self._plugins)) or "(none)"
            raise PluginNotFoundError(
                f"Plugin '{name}' not found. Available: {available}"
            )
        return self._plugins[name]

    def list_plugins(self) -> list[dict[str, Any]]:
        """Return metadata for all registered plugins."""
        return [
            {
                "name": m.name,
                "version": m.version,
                "display_name": m.display_name,
                "description": m.description,
                "team": m.team,
                "categories": m.categories,
                "base_url": m.base_url,
                "tools": m.tool_names,
                "has_service": m.service is not None,
                "depends_on": m.depends_on,
            }
            for m in self._plugins.values()
        ]

    def get_tool(self, tool_name: str) -> tuple[PluginManifest, PluginToolSpec] | None:
        """Look up which plugin provides a tool and its spec."""
        entry = self._tool_index.get(tool_name)
        if entry is None:
            return None
        plugin_name, tool_spec = entry
        return self._plugins[plugin_name], tool_spec

    def list_tools(self) -> list[dict[str, Any]]:
        """List all tools across all plugins."""
        return [
            {
                "name": tool_spec.name,
                "plugin": plugin_name,
                "description": tool_spec.description,
                "endpoint": tool_spec.endpoint,
            }
            for tool_name, (plugin_name, tool_spec) in self._tool_index.items()
        ]

    def get_plugins_subscribing_to(self, event_type: str) -> list[PluginManifest]:
        """Find all plugins that subscribe to a given event type."""
        return [
            m for m in self._plugins.values()
            if event_type in m.events.subscribes
        ]

    def get_plugins_with_service(self) -> list[PluginManifest]:
        """Get all plugins that can run as workspace sidecars."""
        return [m for m in self._plugins.values() if m.service is not None]

    def has_plugin(self, name: str) -> bool:
        return name in self._plugins

    def _remove_tool_index(self, plugin_name: str) -> None:
        to_remove = [
            tool_name for tool_name, (pname, _) in self._tool_index.items()
            if pname == plugin_name
        ]
        for tool_name in to_remove:
            del self._tool_index[tool_name]


# Singleton instance — imported by other modules
plugin_registry = PluginRegistry()
