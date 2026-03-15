"""Prometheus metrics for the PyWorkspace platform."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# Workspace metrics
WORKSPACE_TOTAL = Gauge(
    "pyws_workspaces_total",
    "Total workspaces by status",
    ["status"],
)

PROVISIONING_DURATION = Histogram(
    "pyws_provisioning_seconds",
    "Workspace provision time in seconds",
    buckets=[5, 10, 20, 30, 45, 60, 90, 120, 180, 300],
)

SERVICE_HEALTH = Gauge(
    "pyws_service_health",
    "Service health status (1=healthy, 0=unhealthy)",
    ["type", "workspace"],
)

AGENT_TASKS = Counter(
    "pyws_agent_tasks_total",
    "Total agent tasks executed",
    ["workspace", "status"],
)

RESOURCE_UTILISATION = Gauge(
    "pyws_resource_utilisation",
    "Resource utilisation percentage",
    ["workspace", "resource"],
)

API_LATENCY = Histogram(
    "pyws_api_latency_seconds",
    "API endpoint latency in seconds",
    ["endpoint", "method"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

# Service catalog metrics
CATALOG_SERVICE_PROVISIONS = Counter(
    "pyws_service_provisions_total",
    "Total service provisions by type",
    ["service_type"],
)
