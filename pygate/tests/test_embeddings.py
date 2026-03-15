"""Tests for embedding endpoints."""

import pytest


def test_basic_embedding(client, auth_headers):
    """POST /v1/embeddings returns 200 and has embeddings list."""
    response = client.post(
        "/v1/embeddings",
        json={"input": "Hello, world!"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "embeddings" in data
    assert isinstance(data["embeddings"], list)
    assert len(data["embeddings"]) == 1
    assert data["id"].startswith("embd-")


def test_embedding_dimensions(client, auth_headers):
    """Embedding vectors have correct length (1536 for text-embedding-3-small)."""
    response = client.post(
        "/v1/embeddings",
        json={"input": "Test text", "model": "text-embedding-3-small"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["embeddings"][0]) == 1536


def test_batch_embeddings(client, auth_headers):
    """Multiple inputs produce multiple embeddings."""
    inputs = ["First text", "Second text", "Third text"]
    response = client.post(
        "/v1/embeddings",
        json={"input": inputs},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["embeddings"]) == 3
    # Each embedding should have the same dimensions
    for emb in data["embeddings"]:
        assert len(emb) == 1536


def test_embedding_returns_usage(client, auth_headers):
    """Response has usage dict."""
    response = client.post(
        "/v1/embeddings",
        json={"input": "Some text for embedding"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "usage" in data
    assert "prompt_tokens" in data["usage"]
    assert "total_tokens" in data["usage"]
    assert data["usage"]["prompt_tokens"] > 0
