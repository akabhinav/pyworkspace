"""Plugin loader — discovers and loads plugin manifests from multiple sources.

Supports:
  1. Local YAML/JSON files (dev, ConfigMap mounts)
  2. HTTP discovery (GET {base_url}/plugin/manifest)
  3. Directory scanning (load all manifests from a directory)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog
import httpx
import yaml

from pyworkspace.plugins.manifest import PluginManifest
from pyworkspace.plugins.registry import PluginRegistry, plugin_registry

logger = structlog.get_logger()


class PluginLoadError(Exception):
    pass


class PluginLoader:
    """Loads plugin manifests from various sources into the registry."""

    def __init__(self, registry: PluginRegistry | None = None) -> None:
        self.registry = registry or plugin_registry

    def load_from_file(self, path: str | Path) -> PluginManifest:
        """Load a single plugin manifest from a YAML or JSON file."""
        path = Path(path)
        if not path.exists():
            raise PluginLoadError(f"Manifest file not found: {path}")

        text = path.read_text()
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(text)
        elif path.suffix == ".json":
            data = json.loads(text)
        else:
            raise PluginLoadError(f"Unsupported manifest format: {path.suffix}")

        manifest = PluginManifest(**data)
        self.registry.register(manifest)
        logger.info("plugin_loaded_from_file", path=str(path), plugin=manifest.name)
        return manifest

    def load_from_directory(self, directory: str | Path) -> list[PluginManifest]:
        """Scan a directory for plugin manifest files and load them all."""
        directory = Path(directory)
        if not directory.is_dir():
            logger.warning("plugin_directory_not_found", path=str(directory))
            return []

        manifests: list[PluginManifest] = []
        for path in sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml")) + sorted(directory.glob("*.json")):
            try:
                manifest = self.load_from_file(path)
                manifests.append(manifest)
            except Exception as e:
                logger.error("plugin_load_failed", path=str(path), error=str(e))

        logger.info("plugins_loaded_from_directory", path=str(directory), count=len(manifests))
        return manifests

    async def load_from_url(self, base_url: str) -> PluginManifest:
        """Discover a plugin by fetching its manifest from HTTP endpoint.

        The plugin is expected to serve its manifest at GET {base_url}/plugin/manifest.
        This is how external services self-register with PyWorkspace.
        """
        manifest_url = f"{base_url.rstrip('/')}/plugin/manifest"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(manifest_url)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise PluginLoadError(
                    f"Failed to fetch manifest from {manifest_url}: {e}"
                )

        data = response.json()
        manifest = PluginManifest(**data)
        self.registry.register(manifest)
        logger.info("plugin_loaded_from_url", url=manifest_url, plugin=manifest.name)
        return manifest

    async def discover_plugins(self, urls: list[str]) -> list[PluginManifest]:
        """Discover multiple plugins from their HTTP endpoints."""
        manifests: list[PluginManifest] = []
        for url in urls:
            try:
                manifest = await self.load_from_url(url)
                manifests.append(manifest)
            except Exception as e:
                logger.error("plugin_discovery_failed", url=url, error=str(e))
        return manifests

    def load_from_dict(self, data: dict[str, Any]) -> PluginManifest:
        """Load a plugin manifest from a dict (e.g., from API request body)."""
        manifest = PluginManifest(**data)
        self.registry.register(manifest)
        logger.info("plugin_loaded_from_dict", plugin=manifest.name)
        return manifest
