"""Tests for plugin manifest endpoint."""


def test_manifest_endpoint(client):
    """GET /plugin/manifest returns 200 with valid manifest."""
    resp = client.get("/plugin/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "pymem"
    assert "version" in data
    assert "description" in data


def test_manifest_has_service(client):
    """Manifest includes service spec."""
    resp = client.get("/plugin/manifest")
    data = resp.json()
    service = data["service"]
    assert service["image"] == "yourorg/pymem:1.0.0"
    assert service["port"] == 8090
    assert "cpu" in service["resources"]
    assert "memory" in service["resources"]
    assert "disk" in service["resources"]


def test_manifest_has_tools(client):
    """Manifest defines 3 tools."""
    resp = client.get("/plugin/manifest")
    data = resp.json()
    tools = data["tools"]
    assert len(tools) == 3
    tool_names = {t["name"] for t in tools}
    assert tool_names == {"knowledge_ingest", "knowledge_search", "knowledge_context"}


def test_manifest_has_events(client):
    """Manifest defines publishes and subscribes events."""
    resp = client.get("/plugin/manifest")
    data = resp.json()
    events = data["events"]
    assert "knowledge.ingested" in events["publishes"]
    assert "knowledge.index.updated" in events["publishes"]
    assert "workspace.destroyed" in events["subscribes"]
