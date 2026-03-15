"""Tests for LLM completion endpoints."""

import pytest


def test_basic_completion(client, auth_headers):
    """POST /v1/completions with messages returns 200 and has content."""
    response = client.post(
        "/v1/completions",
        json={
            "messages": [{"role": "user", "content": "Hello, world!"}],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert len(data["content"]) > 0
    assert data["id"].startswith("cmpl-")


def test_completion_with_different_models(client, auth_headers):
    """Test completions with claude, gpt-4o, and llama models."""
    models = ["claude-sonnet-4-20250514", "gpt-4o", "llama-3.1-70b"]
    for model in models:
        response = client.post(
            "/v1/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Test prompt"}],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200, f"Failed for model {model}"
        data = response.json()
        assert data["model"] == model
        assert f"[{model}]" in data["content"]


def test_completion_unknown_model(client, auth_headers):
    """Unknown model returns 400."""
    response = client.post(
        "/v1/completions",
        json={
            "model": "nonexistent-model",
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_completion_returns_usage(client, auth_headers):
    """Response has usage dict with token counts."""
    response = client.post(
        "/v1/completions",
        json={
            "messages": [{"role": "user", "content": "Tell me a joke"}],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    usage = data["usage"]
    assert "prompt_tokens" in usage
    assert "completion_tokens" in usage
    assert "total_tokens" in usage
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
    assert usage["prompt_tokens"] > 0
    assert usage["completion_tokens"] > 0


def test_completion_returns_provider(client, auth_headers):
    """Response has provider field matching the model's provider."""
    response = client.post(
        "/v1/completions",
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"


def test_auth_required(client):
    """Request without Authorization header returns 401."""
    response = client.post(
        "/v1/completions",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert response.status_code == 401
