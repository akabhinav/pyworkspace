from pyworkspace.observability.tracing import setup_tracing


class TestTracing:
    def test_setup_tracing_disabled(self):
        # With no OTEL_ENDPOINT, tracing should be disabled (no error)
        setup_tracing()
