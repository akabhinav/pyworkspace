"""Tests for semantic search."""


def test_basic_search(client, auth_headers):
    """Ingest text about Python data science, search 'python data' finds it."""
    client.post(
        "/v1/ingest",
        json={"content": "Python is great for data science and machine learning."},
        headers=auth_headers,
    )
    resp = client.post(
        "/v1/search",
        json={"query": "python data"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_results"] > 0
    assert "python" in data["results"][0]["content"].lower()


def test_search_ranking(client, auth_headers):
    """Ingest 3 docs, search returns most relevant first."""
    client.post(
        "/v1/ingest",
        json={"content": "Cooking recipes for pasta and pizza."},
        headers=auth_headers,
    )
    client.post(
        "/v1/ingest",
        json={"content": "Python programming for data science and analytics."},
        headers=auth_headers,
    )
    client.post(
        "/v1/ingest",
        json={"content": "Gardening tips for spring flowers."},
        headers=auth_headers,
    )

    resp = client.post(
        "/v1/search",
        json={"query": "python data science"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 0
    # The Python doc should be ranked first
    assert "python" in results[0]["content"].lower()
    assert "data" in results[0]["content"].lower()


def test_search_top_k(client, auth_headers):
    """top_k=1 returns only 1 result."""
    for i in range(5):
        client.post(
            "/v1/ingest",
            json={"content": f"Document {i} about python programming."},
            headers=auth_headers,
        )

    resp = client.post(
        "/v1/search",
        json={"query": "python", "top_k": 1},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total_results"] == 1


def test_search_empty_store(client, auth_headers):
    """Search on empty store returns empty results."""
    resp = client.post(
        "/v1/search",
        json={"query": "python"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total_results"] == 0
    assert resp.json()["results"] == []


def test_search_no_match(client, auth_headers):
    """Search gibberish returns no results or low scores."""
    client.post(
        "/v1/ingest",
        json={"content": "Python is great for data science."},
        headers=auth_headers,
    )
    resp = client.post(
        "/v1/search",
        json={"query": "xyzzy qqqqq zzzzzz", "min_score": 0.1},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total_results"] == 0
