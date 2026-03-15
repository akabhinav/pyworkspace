"""Event bus for decoupled cross-component communication.

Components publish events (e.g., workspace.created, sandbox.completed).
Other components subscribe — either via in-process handlers or HTTP webhooks.
This enables loose coupling: PyWorkspace doesn't need to know about PyReview,
it just publishes workspace.created and any subscriber reacts.
"""

from pyworkspace.events.bus import EventBus, event_bus
from pyworkspace.events.types import Event, EventType

__all__ = ["EventBus", "event_bus", "Event", "EventType"]
