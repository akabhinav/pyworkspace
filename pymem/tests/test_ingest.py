"""Tests for document ingestion."""


def test_ingest_text(client, auth_headers):
    """POST /v1/ingest with content returns 200, document_id, and chunks > 0."""
    resp = client.post(
        "/v1/ingest",
        json={"content": "Python is a great programming language for data science."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "document_id" in data
    assert data["chunks_created"] > 0
    assert data["status"] == "ingested"


def test_ingest_with_metadata(client, auth_headers):
    """Metadata is stored correctly on ingest."""
    resp = client.post(
        "/v1/ingest",
        json={
            "content": "Some content about machine learning.",
            "metadata": {"topic": "ml", "author": "test"},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    doc_id = resp.json()["document_id"]

    # Verify metadata is stored by fetching the document
    doc_resp = client.get(f"/v1/documents/{doc_id}", headers=auth_headers)
    assert doc_resp.status_code == 200
    assert doc_resp.json()["metadata"]["topic"] == "ml"
    assert doc_resp.json()["metadata"]["author"] == "test"


def test_ingest_creates_chunks(client, auth_headers):
    """Content of 1500 chars with chunk_size=500 creates 3+ chunks."""
    content = "a" * 1500
    resp = client.post(
        "/v1/ingest",
        json={"content": content, "chunk_size": 500, "overlap": 50},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["chunks_created"] >= 3


def test_ingest_multiple_documents(client, auth_headers):
    """Ingesting 3 documents results in 3 listed documents."""
    for i in range(3):
        resp = client.post(
            "/v1/ingest",
            json={"content": f"Document number {i} with unique content."},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    docs_resp = client.get("/v1/documents", headers=auth_headers)
    assert docs_resp.status_code == 200
    assert len(docs_resp.json()) == 3


def test_auth_required(client):
    """Request without auth returns 401 or 403."""
    resp = client.post(
        "/v1/ingest",
        json={"content": "test content"},
    )
    assert resp.status_code in (401, 403)
