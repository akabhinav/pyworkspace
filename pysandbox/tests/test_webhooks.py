from pysandbox.sandbox_manager import sandbox_manager


def test_workspace_created_event(client):
    response = client.post(
        "/webhooks/events",
        json={"event_type": "workspace.created", "workspace_id": "ws-123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["event_type"] == "workspace.created"

    # Verify a sandbox was pre-warmed
    sandboxes = sandbox_manager.list_sandboxes()
    assert len(sandboxes) >= 1
    assert any(s.workspace_id == "ws-123" for s in sandboxes)


def test_workspace_destroyed_event(client):
    # First create a sandbox for this workspace
    sandbox_manager.create_sandbox(workspace_id="ws-456")

    response = client.post(
        "/webhooks/events",
        json={"event_type": "workspace.destroyed", "workspace_id": "ws-456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["event_type"] == "workspace.destroyed"

    # Verify sandboxes were cleaned up
    sandboxes = sandbox_manager.list_sandboxes()
    assert not any(s.workspace_id == "ws-456" for s in sandboxes)


def test_unknown_event(client):
    response = client.post(
        "/webhooks/events",
        json={"event_type": "unknown.event", "some_data": "value"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["event_type"] == "unknown.event"
