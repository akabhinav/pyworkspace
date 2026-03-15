"""OpenTelemetry tracing setup."""

from __future__ import annotations

import structlog

from pyworkspace.config.settings import get_settings

logger = structlog.get_logger()


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing if configured."""
    settings = get_settings()
    if not settings.OTEL_ENDPOINT:
        logger.info("tracing_disabled", reason="no OTEL_ENDPOINT configured")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": "pyworkspace",
                "service.version": settings.PYWORKSPACE_VERSION,
            }
        )

        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_ENDPOINT)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        logger.info("tracing_enabled", endpoint=settings.OTEL_ENDPOINT)
    except ImportError:
        logger.warning("tracing_setup_failed", reason="opentelemetry packages not installed")
    except Exception as e:
        logger.warning("tracing_setup_failed", error=str(e))
