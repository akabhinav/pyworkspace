"""FastAPI application factory with lifespan hooks."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager

import logging

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pyworkspace.config.settings import get_settings


def configure_logging() -> None:
    """Configure structlog for JSON output."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            (
                structlog.dev.ConsoleRenderer()
                if get_settings().PYWORKSPACE_ENV == "dev"
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(get_settings().LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    logger = structlog.get_logger()
    settings = get_settings()

    logger.info(
        "pyworkspace_starting",
        version=settings.PYWORKSPACE_VERSION,
        env=settings.PYWORKSPACE_ENV,
    )

    # Initialize tracing
    from pyworkspace.observability.tracing import setup_tracing

    setup_tracing()

    # Load plugins from manifest directory and discovery URLs
    await _load_plugins(logger, settings)

    yield

    logger.info("pyworkspace_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title="PyWorkspace",
        description="Enterprise Environment-as-a-Service platform",
        version=settings.PYWORKSPACE_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.PYWORKSPACE_ENV == "dev" else [],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import catalog modules to trigger @register_service decorators
    _register_catalog()

    # Mount routers
    from pyworkspace.api.health import router as health_router
    from pyworkspace.api.v1 import v1_router

    app.include_router(health_router)
    app.include_router(v1_router)

    return app


def _register_catalog() -> None:
    """Import all catalog modules to trigger service registration."""
    import pyworkspace.catalog.databases  # noqa: F401
    import pyworkspace.catalog.cache  # noqa: F401
    import pyworkspace.catalog.messaging  # noqa: F401
    import pyworkspace.catalog.cloud  # noqa: F401
    import pyworkspace.catalog.runtime  # noqa: F401
    import pyworkspace.catalog.monitoring  # noqa: F401
    import pyworkspace.catalog.search  # noqa: F401


async def _load_plugins(logger, settings) -> None:
    """Load plugins from filesystem manifests and HTTP discovery on startup."""
    from pyworkspace.plugins.loader import PluginLoader
    from pyworkspace.events import event_bus

    loader = PluginLoader()

    # 1. Load from manifest directory (YAML/JSON files, e.g., from ConfigMap)
    manifest_dir = settings.PLUGIN_MANIFEST_DIR
    manifests = loader.load_from_directory(manifest_dir)
    for m in manifests:
        if m.events.callback_url:
            for event_type in m.events.subscribes:
                event_bus.subscribe_webhook(event_type, m.events.callback_url)

    # 2. Discover from HTTP endpoints
    if settings.PLUGIN_DISCOVERY_URLS:
        urls = [u.strip() for u in settings.PLUGIN_DISCOVERY_URLS.split(",") if u.strip()]
        discovered = await loader.discover_plugins(urls)
        for m in discovered:
            if m.events.callback_url:
                for event_type in m.events.subscribes:
                    event_bus.subscribe_webhook(event_type, m.events.callback_url)

    logger.info(
        "plugins_loaded",
        from_files=len(manifests),
        from_discovery=len(discovered) if settings.PLUGIN_DISCOVERY_URLS else 0,
    )


app = create_app()
