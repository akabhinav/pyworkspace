from pyworkspace.events.types import Event, EventType


class TestEventType:
    def test_workspace_events(self):
        assert EventType.WORKSPACE_CREATED == "workspace.created"
        assert EventType.WORKSPACE_DESTROYED == "workspace.destroyed"

    def test_service_events(self):
        assert EventType.SERVICE_STARTED == "service.started"
        assert EventType.SERVICE_HEALTHY == "service.healthy"

    def test_agent_events(self):
        assert EventType.AGENT_STARTED == "agent.started"

    def test_plugin_events(self):
        assert EventType.PLUGIN_REGISTERED == "plugin.registered"

    def test_snapshot_events(self):
        assert EventType.SNAPSHOT_CREATED == "snapshot.created"


class TestEvent:
    def test_create_event(self):
        event = Event(
            event_type=EventType.WORKSPACE_CREATED,
            source="pyworkspace",
            workspace_id="ws-1",
            org_id="org-1",
            payload={"name": "test-workspace"},
        )
        assert event.event_type == "workspace.created"
        assert event.workspace_id == "ws-1"
        assert event.event_id  # auto-generated
        assert event.retry_count == 0

    def test_event_serialization(self):
        event = Event(
            event_type="custom.event",
            source="test",
        )
        data = event.model_dump(mode="json")
        assert data["event_type"] == "custom.event"
        assert "timestamp" in data
        assert "event_id" in data

    def test_event_defaults(self):
        event = Event(event_type="test", source="test")
        assert event.workspace_id is None
        assert event.org_id is None
        assert event.payload == {}
