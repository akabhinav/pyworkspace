from pyworkspace.observability.metrics import (
    AGENT_TASKS,
    API_LATENCY,
    CATALOG_SERVICE_PROVISIONS,
    PROVISIONING_DURATION,
    RESOURCE_UTILISATION,
    SERVICE_HEALTH,
    WORKSPACE_TOTAL,
)


class TestMetrics:
    def test_workspace_total_gauge(self):
        WORKSPACE_TOTAL.labels(status="running").set(5)
        assert WORKSPACE_TOTAL.labels(status="running")._value.get() == 5.0

    def test_provisioning_duration_histogram(self):
        PROVISIONING_DURATION.observe(15.0)
        # Just verify it doesn't raise

    def test_service_health_gauge(self):
        SERVICE_HEALTH.labels(type="postgres", workspace="ws-1").set(1)
        assert SERVICE_HEALTH.labels(type="postgres", workspace="ws-1")._value.get() == 1.0

    def test_agent_tasks_counter(self):
        AGENT_TASKS.labels(workspace="ws-1", status="completed").inc()
        # Just verify it doesn't raise

    def test_api_latency_histogram(self):
        API_LATENCY.labels(endpoint="/v1/workspaces", method="GET").observe(0.05)
        # Just verify it doesn't raise

    def test_catalog_provisions_counter(self):
        CATALOG_SERVICE_PROVISIONS.labels(service_type="postgres").inc()
        # Just verify it doesn't raise
