"""Cloud service catalog — auto-imports all cloud service definitions."""

from __future__ import annotations

from pyworkspace.catalog.cloud.localstack import LocalStackService
from pyworkspace.catalog.cloud.minio import MinIOService

__all__ = [
    "LocalStackService",
    "MinIOService",
]
