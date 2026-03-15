"""Search service catalog — auto-imports all search service definitions."""

from __future__ import annotations

from pyworkspace.catalog.search.opensearch import OpenSearchService

__all__ = [
    "OpenSearchService",
]
