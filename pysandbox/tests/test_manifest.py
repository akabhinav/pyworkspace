def test_manifest_endpoint(client):
    response = client.get("/plugin/manifest")
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "PyWorkspacePlugin"
    assert data["name"] == "pysandbox"
    assert data["version"] == "1.0.0"
    assert data["display_name"] == "PySandbox"
    assert data["api_version"] == "v1"
    assert data["auth_type"] == "api_key"


def test_manifest_has_tools(client):
    response = client.get("/plugin/manifest")
    data = response.json()
    tools = data["tools"]
    assert len(tools) == 3
    tool_names = {t["name"] for t in tools}
    assert "sandbox_create" in tool_names
    assert "sandbox_execute" in tool_names
    assert "sandbox_destroy" in tool_names


def test_manifest_has_events(client):
    response = client.get("/plugin/manifest")
    data = response.json()
    events = data["events"]
    assert "publishes" in events
    assert "subscribes" in events
    assert "sandbox.created" in events["publishes"]
    assert "workspace.created" in events["subscribes"]
    assert "workspace.destroyed" in events["subscribes"]
