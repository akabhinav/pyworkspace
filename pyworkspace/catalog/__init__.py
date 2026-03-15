"""Service catalog — pluggable service definitions for workspaces."""

from __future__ import annotations

from pyworkspace.catalog.registry import (
    get_service_definition,
    list_services,
    register_service,
)

__all__ = [
    "get_service_definition",
    "list_services",
    "register_service",
]
