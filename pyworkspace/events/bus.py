"""Event bus — publish/subscribe with in-process handlers + webhook delivery.

Supports two subscriber types:
  1. In-process async handlers (for PyWorkspace's own modules)
  2. HTTP webhook callbacks (for external plugins — PyReview, PySandbox, etc.)

External plugins declare their subscriptions in their manifest:
    events:
      subscribes: [workspace.created, workspace.destroyed]
      callback_url: http://pyreview.internal:8080/webhooks/events

When an event is published, the bus:
  1. Calls all in-process handlers
  2. POSTs the event JSON to all matching webhook URLs
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine

import httpx
import structlog

from pyworkspace.events.types import Event

logger = structlog.get_logger()

# Type alias for async event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """Async event bus with in-process and webhook delivery."""

    def __init__(self) -> None:
        # In-process handlers: event_type → [handler_fn, ...]
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        # Webhook subscribers: event_type → [callback_url, ...]
        self._webhooks: dict[str, list[str]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register an in-process async handler for an event type."""
        self._handlers[event_type].append(handler)
        logger.debug("event_handler_registered", event_type=event_type)

    def subscribe_webhook(self, event_type: str, callback_url: str) -> None:
        """Register a webhook URL for an event type (used by external plugins)."""
        if callback_url not in self._webhooks[event_type]:
            self._webhooks[event_type].append(callback_url)
            logger.info(
                "webhook_registered",
                event_type=event_type,
                callback_url=callback_url,
            )

    def unsubscribe_webhook(self, event_type: str, callback_url: str) -> None:
        """Remove a webhook subscription."""
        urls = self._webhooks.get(event_type, [])
        if callback_url in urls:
            urls.remove(callback_url)

    def unsubscribe_all_webhooks(self, callback_url: str) -> None:
        """Remove all webhook subscriptions for a given URL (used on plugin unregister)."""
        for event_type in self._webhooks:
            urls = self._webhooks[event_type]
            if callback_url in urls:
                urls.remove(callback_url)

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers (handlers + webhooks).

        In-process handlers run concurrently. Webhook delivery is fire-and-forget
        with error logging (no retry in this layer — use a task queue for that).
        """
        event_type = event.event_type

        # In-process handlers
        handlers = self._handlers.get(event_type, [])
        if handlers:
            results = await asyncio.gather(
                *[self._safe_call(h, event) for h in handlers],
                return_exceptions=True,
            )
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "event_handler_failed",
                        event_type=event_type,
                        error=str(result),
                    )

        # Webhook delivery
        webhooks = self._webhooks.get(event_type, [])
        if webhooks:
            await asyncio.gather(
                *[self._deliver_webhook(url, event) for url in webhooks],
                return_exceptions=True,
            )

        logger.debug(
            "event_published",
            event_type=event_type,
            handlers=len(handlers),
            webhooks=len(webhooks),
            event_id=event.event_id,
        )

    async def _safe_call(self, handler: EventHandler, event: Event) -> None:
        try:
            await handler(event)
        except Exception:
            logger.exception("event_handler_error", event_type=event.event_type)
            raise

    async def _deliver_webhook(self, url: str, event: Event) -> None:
        """POST event JSON to a webhook URL. Fire-and-forget with logging."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json=event.model_dump(mode="json"),
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code >= 400:
                    logger.warning(
                        "webhook_delivery_failed",
                        url=url,
                        status=response.status_code,
                        event_type=event.event_type,
                    )
        except Exception as e:
            logger.warning(
                "webhook_delivery_error",
                url=url,
                event_type=event.event_type,
                error=str(e),
            )


# Singleton instance
event_bus = EventBus()
