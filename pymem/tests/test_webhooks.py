"""Tests for event webhook handling."""


def test_workspace_destroyed_cleanup(client, auth_headers):
    """POST workspace.destroyed cleans up docs for that workspace."""
    workspace_id = "ws-test-123"

    # Ingest docs tagged with workspace_id
    for i in range(3):
        client.post(
            "/v1/ingest",
            json={
                "content": f"Document {i} for workspace.",
                "metadata": {"workspace_id": workspace_id},
            },
            headers=auth_headers,
        )

    # Ingest a doc for a different workspace
    client.post(
        "/v1/ingest",
        json={
            "content": "Document for other workspace.",
            "metadata": {"workspace_id": "ws-other"},
        },
        headers=auth_headers,
    )

    # Verify 4 total docs
    docs = client.get("/v1/documents", headers=auth_headers).json()
    assert len(docs) == 4

    # Send workspace.destroyed event
    resp = client.post(
        "/webhooks/events",
        json={"event": "workspace.destroyed", "workspace_id": workspace_id},
    )
    assert resp.status_code == 200
    assert resp.json()["documents_removed"] == 3

    # Verify only 1 doc remains
    docs = client.get("/v1/documents", headers=auth_headers).json()
    assert len(docs) == 1
    assert docs[0]["metadata"]["workspace_id"] == "ws-other"


def test_unknown_event_accepted(client):
    """POST random event returns 200."""
    resp = client.post(
        "/webhooks/events",
        json={"event": "some.random.event", "data": {"key": "value"}},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
