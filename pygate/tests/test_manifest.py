"""Tests for the plugin manifest endpoint."""

import pytest


def test_manifest_returns_valid_json(client):
    """GET /plugin/manifest returns 200 with valid JSON."""
    response = client.get("/plugin/manifest")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "pygate"
    assert data["version"] == "1.0.0"


def test_manifest_no_service(client):
    """Service field is None (standalone plugin)."""
    response = client.get("/plugin/manifest")
    data = response.json()
    assert data["service"] is None


def test_manifest_has_tools(client):
    """Manifest has exactly 2 tools defined."""
    response = client.get("/plugin/manifest")
    data = response.json()
    assert len(data["tools"]) == 2
    tool_names = [t["name"] for t in data["tools"]]
    assert "llm_complete" in tool_names
    assert "llm_embed" in tool_names


def test_manifest_is_standalone(client):
    """Manifest has no service spec, confirming standalone mode."""
    response = client.get("/plugin/manifest")
    data = response.json()
    assert data["service"] is None
    # Events should exist
    assert "publishes" in data["events"]
    assert "subscribes" in data["events"]
    assert len(data["events"]["subscribes"]) == 0
