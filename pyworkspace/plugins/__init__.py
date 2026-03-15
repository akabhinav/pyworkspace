"""Plugin system for loosely-coupled, runtime service/tool registration."""

from pyworkspace.plugins.manifest import PluginManifest, PluginToolSpec, PluginServiceSpec
from pyworkspace.plugins.registry import PluginRegistry
from pyworkspace.plugins.loader import PluginLoader

__all__ = [
    "PluginManifest",
    "PluginToolSpec",
    "PluginServiceSpec",
    "PluginRegistry",
    "PluginLoader",
]
