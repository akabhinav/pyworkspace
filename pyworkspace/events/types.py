"""Event type definitions — the shared vocabulary across all components."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventType(StrEnum):
    """Well-known event types in the PyWorkspace platform.

    Components can also use custom event types (any string).
    These are the standard ones that PyWorkspace itself publishes.
    """
    # Workspace lifecycle
    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_PROVISIONED = "workspace.provisioned"
    WORKSPACE_PAUSED = "workspace.paused"
    WORKSPACE_RESUMED = "workspace.resumed"
    WORKSPACE_DESTROYED = "workspace.destroyed"
    WORKSPACE_ERROR = "workspace.error"

    # Service lifecycle
    SERVICE_STARTED = "service.started"
    SERVICE_HEALTHY = "service.healthy"
    SERVICE_UNHEALTHY = "service.unhealthy"
    SERVICE_STOPPED = "service.stopped"

    # Agent
    AGENT_STARTED = "agent.started"
    AGENT_TASK_COMPLETED = "agent.task.completed"
    AGENT_TASK_FAILED = "agent.task.failed"

    # Plugin lifecycle
    PLUGIN_REGISTERED = "plugin.registered"
    PLUGIN_UNREGISTERED = "plugin.unregistered"
    PLUGIN_HEALTH_CHANGED = "plugin.health.changed"

    # Snapshot
    SNAPSHOT_CREATED = "snapshot.created"
    SNAPSHOT_RESTORED = "snapshot.restored"


class Event(BaseModel):
    """A platform event that flows through the event bus.

    Every event has a type, source, and payload. Components receive
    this as a JSON POST body at their callback_url.
    """
    event_type: str
    source: str  # e.g., "pyworkspace", "pysandbox", "pyreview"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Context
    workspace_id: str | None = None
    org_id: str | None = None

    # Arbitrary payload — each event type defines its own shape
    payload: dict[str, Any] = Field(default_factory=dict)

    # Delivery metadata
    event_id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    retry_count: int = 0
