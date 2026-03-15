"""Plugin management API — external components register/unregister here.

This is how teams ship independently:
  1. Team deploys their service (e.g., PySandbox)
  2. On startup, PySandbox POSTs its manifest to POST /v1/plugins/register
  3. PyWorkspace discovers its tools, service spec, and event subscriptions
  4. No code changes in PyWorkspace needed

Alternatively, plugins can be pre-loaded from YAML files on disk
(e.g., mounted as a ConfigMap in K8s).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from pyworkspace.events import Event, EventType, event_bus
from pyworkspace.plugins.loader import PluginLoader
from pyworkspace.plugins.manifest import PluginManifest
from pyworkspace.plugins.registry import PluginNotFoundError, plugin_registry

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_plugin(manifest: PluginManifest) -> dict[str, Any]:
    """Register or update a plugin from its manifest.

    Called by external components on startup:
        POST /v1/plugins/register
        Body: { "name": "pysandbox", "base_url": "http://...", ... }
    """
    loader = PluginLoader()
    loader.load_from_dict(manifest.model_dump())

    # Wire up webhook subscriptions from the manifest
    if manifest.events.callback_url:
        for event_type in manifest.events.subscribes:
            event_bus.subscribe_webhook(event_type, manifest.events.callback_url)

    # Publish plugin.registered event
    await event_bus.publish(Event(
        event_type=EventType.PLUGIN_REGISTERED,
        source="pyworkspace",
        payload={
            "plugin": manifest.name,
            "version": manifest.version,
            "tools": manifest.tool_names,
        },
    ))

    return {
        "status": "registered",
        "plugin": manifest.name,
        "version": manifest.version,
        "tools": manifest.tool_names,
        "service_available": manifest.service is not None,
    }


@router.delete("/{plugin_name}", status_code=status.HTTP_200_OK)
async def unregister_plugin(plugin_name: str) -> dict[str, str]:
    """Unregister a plugin. Called on component shutdown or admin action."""
    try:
        manifest = plugin_registry.get(plugin_name)
    except PluginNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_name}' not found",
        )

    # Remove webhook subscriptions
    if manifest.events.callback_url:
        event_bus.unsubscribe_all_webhooks(manifest.events.callback_url)

    plugin_registry.unregister(plugin_name)

    await event_bus.publish(Event(
        event_type=EventType.PLUGIN_UNREGISTERED,
        source="pyworkspace",
        payload={"plugin": plugin_name},
    ))

    return {"status": "unregistered", "plugin": plugin_name}


@router.get("", status_code=status.HTTP_200_OK)
async def list_plugins() -> list[dict[str, Any]]:
    """List all registered plugins and their metadata."""
    return plugin_registry.list_plugins()


@router.get("/{plugin_name}", status_code=status.HTTP_200_OK)
async def get_plugin(plugin_name: str) -> dict[str, Any]:
    """Get details for a specific plugin."""
    try:
        manifest = plugin_registry.get(plugin_name)
    except PluginNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_name}' not found",
        )
    return manifest.model_dump()


@router.get("/{plugin_name}/tools", status_code=status.HTTP_200_OK)
async def list_plugin_tools(plugin_name: str) -> list[dict[str, Any]]:
    """List tools provided by a specific plugin."""
    try:
        manifest = plugin_registry.get(plugin_name)
    except PluginNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_name}' not found",
        )
    return [t.model_dump() for t in manifest.tools]


@router.post("/discover", status_code=status.HTTP_200_OK)
async def discover_plugins(urls: list[str]) -> dict[str, Any]:
    """Discover and register plugins from their HTTP endpoints.

    POST /v1/plugins/discover
    Body: ["http://pysandbox.internal:8080", "http://pygate.internal:8443"]
    """
    loader = PluginLoader()
    manifests = await loader.discover_plugins(urls)

    # Wire up webhooks for discovered plugins
    for manifest in manifests:
        if manifest.events.callback_url:
            for event_type in manifest.events.subscribes:
                event_bus.subscribe_webhook(event_type, manifest.events.callback_url)

    return {
        "discovered": len(manifests),
        "plugins": [
            {"name": m.name, "version": m.version, "tools": m.tool_names}
            for m in manifests
        ],
    }
