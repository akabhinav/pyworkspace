"""Tests for RAG context assembly."""


def test_context_assembly(client, auth_headers):
    """Ingest docs, request context returns assembled text."""
    client.post(
        "/v1/ingest",
        json={"content": "Python is widely used in data science and analytics."},
        headers=auth_headers,
    )
    client.post(
        "/v1/ingest",
        json={"content": "Machine learning models can be trained with Python."},
        headers=auth_headers,
    )

    resp = client.post(
        "/v1/context",
        json={"query": "python data science"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["context"]) > 0
    assert data["query"] == "python data science"


def test_context_has_sources(client, auth_headers):
    """Context response includes source references."""
    client.post(
        "/v1/ingest",
        json={"content": "Deep learning is a subset of machine learning."},
        headers=auth_headers,
    )
    resp = client.post(
        "/v1/context",
        json={"query": "deep learning"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sources"]) > 0
    # Each source should have chunk_id and document_id
    for source in data["sources"]:
        assert "chunk_id" in source
        assert "document_id" in source


def test_context_respects_max_tokens(client, auth_headers):
    """Context length is within max_tokens limit."""
    # Ingest a large document
    content = "Python programming " * 500  # ~10000 chars
    client.post(
        "/v1/ingest",
        json={"content": content},
        headers=auth_headers,
    )

    max_tokens = 100
    resp = client.post(
        "/v1/context",
        json={"query": "python", "max_tokens": max_tokens},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Context should be roughly within max_tokens * 4 chars
    assert len(data["context"]) <= max_tokens * 4 + 100  # small tolerance


def test_context_from_multiple_docs(client, auth_headers):
    """Context pulls from multiple documents."""
    client.post(
        "/v1/ingest",
        json={"content": "Python is great for web development with Django."},
        headers=auth_headers,
    )
    client.post(
        "/v1/ingest",
        json={"content": "Python excels at data analysis with pandas."},
        headers=auth_headers,
    )
    client.post(
        "/v1/ingest",
        json={"content": "Python supports machine learning with scikit-learn."},
        headers=auth_headers,
    )

    resp = client.post(
        "/v1/context",
        json={"query": "python", "top_k": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Should have sources from multiple docs
    doc_ids = {s["document_id"] for s in data["sources"]}
    assert len(doc_ids) >= 2
