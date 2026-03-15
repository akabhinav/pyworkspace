"""Monitoring service catalog — auto-imports all monitoring service definitions."""

from __future__ import annotations

from pyworkspace.catalog.monitoring.grafana import GrafanaService
from pyworkspace.catalog.monitoring.jaeger import JaegerService
from pyworkspace.catalog.monitoring.loki import LokiService
from pyworkspace.catalog.monitoring.prometheus import PrometheusService

__all__ = [
    "GrafanaService",
    "JaegerService",
    "LokiService",
    "PrometheusService",
]
