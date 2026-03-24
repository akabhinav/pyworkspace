import pytest

from pyworkspace.events.bus import EventBus
from pyworkspace.events.types import Event, EventType


class TestEventBus:
    def setup_method(self):
        self.bus = EventBus()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        received = []

        async def handler(event: Event):
            received.append(event)

        self.bus.subscribe("workspace.created", handler)
        event = Event(event_type="workspace.created", source="test")
        await self.bus.publish(event)

        assert len(received) == 1
        assert received[0].event_type == "workspace.created"

    @pytest.mark.asyncio
    async def test_no_subscribers(self):
        event = Event(event_type="unhandled.event", source="test")
        await self.bus.publish(event)  # Should not raise

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        count = {"value": 0}

        async def handler1(event):
            count["value"] += 1

        async def handler2(event):
            count["value"] += 10

        self.bus.subscribe("test.event", handler1)
        self.bus.subscribe("test.event", handler2)
        await self.bus.publish(Event(event_type="test.event", source="test"))

        assert count["value"] == 11

    def test_subscribe_webhook(self):
        self.bus.subscribe_webhook("workspace.created", "http://plugin:8080/webhook")
        assert "http://plugin:8080/webhook" in self.bus._webhooks["workspace.created"]

    def test_subscribe_webhook_idempotent(self):
        self.bus.subscribe_webhook("test", "http://url")
        self.bus.subscribe_webhook("test", "http://url")
        assert len(self.bus._webhooks["test"]) == 1

    def test_unsubscribe_webhook(self):
        self.bus.subscribe_webhook("test", "http://url")
        self.bus.unsubscribe_webhook("test", "http://url")
        assert "http://url" not in self.bus._webhooks["test"]

    def test_unsubscribe_all_webhooks(self):
        self.bus.subscribe_webhook("event1", "http://url")
        self.bus.subscribe_webhook("event2", "http://url")
        self.bus.unsubscribe_all_webhooks("http://url")
        assert "http://url" not in self.bus._webhooks["event1"]
        assert "http://url" not in self.bus._webhooks["event2"]

    @pytest.mark.asyncio
    async def test_handler_error_doesnt_break_publish(self):
        received = []

        async def bad_handler(event):
            raise ValueError("boom")

        async def good_handler(event):
            received.append(event)

        self.bus.subscribe("test", bad_handler)
        self.bus.subscribe("test", good_handler)
        await self.bus.publish(Event(event_type="test", source="test"))

        assert len(received) == 1
