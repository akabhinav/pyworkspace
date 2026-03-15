"""Tests for LLM routing logic."""

import pytest

from pygate.router import LLMRouter
from pygate.models import CompletionRequest, ModelInfo


def test_model_registry():
    """All 3 models are present in the registry."""
    router = LLMRouter()
    assert "claude-sonnet-4-20250514" in router.MODELS
    assert "gpt-4o" in router.MODELS
    assert "llama-3.1-70b" in router.MODELS


def test_list_models():
    """list_models returns a list of ModelInfo objects."""
    router = LLMRouter()
    models = router.list_models()
    assert len(models) == 3
    for model in models:
        assert isinstance(model, ModelInfo)
        assert model.name in router.MODELS
        assert model.provider in ("anthropic", "openai", "local")


@pytest.mark.asyncio
async def test_request_counting():
    """Requests increment the counter."""
    router = LLMRouter()
    assert router.get_usage()["total_requests"] == 0

    await router.complete(
        CompletionRequest(messages=[{"role": "user", "content": "Hello"}])
    )
    assert router.get_usage()["total_requests"] == 1

    await router.complete(
        CompletionRequest(messages=[{"role": "user", "content": "World"}])
    )
    assert router.get_usage()["total_requests"] == 2


def test_usage_stats(client, auth_headers):
    """Usage endpoint returns stats."""
    response = client.get("/v1/usage", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_prompt_tokens" in data
    assert "total_completion_tokens" in data
    assert "total_tokens" in data
