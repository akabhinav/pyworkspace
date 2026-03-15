def test_create_sandbox(client, auth_headers):
    response = client.post(
        "/v1/sandbox/create",
        json={"language": "python", "timeout_seconds": 300, "memory_mb": 512},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "sandbox_id" in data
    assert data["status"] == "running"
    assert "created_at" in data


def test_execute_code(client, auth_headers):
    # Create sandbox first
    create_resp = client.post(
        "/v1/sandbox/create",
        json={"language": "python"},
        headers=auth_headers,
    )
    sandbox_id = create_resp.json()["sandbox_id"]

    # Execute code
    response = client.post(
        "/v1/sandbox/execute",
        json={"sandbox_id": sandbox_id, "code": "x = 1 + 2"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sandbox_id"] == sandbox_id
    assert data["exit_code"] == 0
    assert "stdout" in data


def test_execute_hello_world(client, auth_headers):
    create_resp = client.post(
        "/v1/sandbox/create",
        json={"language": "python"},
        headers=auth_headers,
    )
    sandbox_id = create_resp.json()["sandbox_id"]

    response = client.post(
        "/v1/sandbox/execute",
        json={"sandbox_id": sandbox_id, "code": "print('hello')"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "hello" in data["stdout"]
    assert data["exit_code"] == 0


def test_execute_error_code(client, auth_headers):
    create_resp = client.post(
        "/v1/sandbox/create",
        json={"language": "python"},
        headers=auth_headers,
    )
    sandbox_id = create_resp.json()["sandbox_id"]

    response = client.post(
        "/v1/sandbox/execute",
        json={"sandbox_id": sandbox_id, "code": "raise ValueError('fail')"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["exit_code"] != 0
    assert data["stderr"] != ""


def test_destroy_sandbox(client, auth_headers):
    create_resp = client.post(
        "/v1/sandbox/create",
        json={"language": "python"},
        headers=auth_headers,
    )
    sandbox_id = create_resp.json()["sandbox_id"]

    response = client.post(
        "/v1/sandbox/destroy",
        json={"sandbox_id": sandbox_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sandbox_id"] == sandbox_id
    assert data["status"] == "destroyed"


def test_execute_nonexistent_sandbox(client, auth_headers):
    response = client.post(
        "/v1/sandbox/execute",
        json={"sandbox_id": "nonexistent-id", "code": "print('hello')"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_list_sandboxes(client, auth_headers):
    # Create 2 sandboxes
    client.post(
        "/v1/sandbox/create",
        json={"language": "python"},
        headers=auth_headers,
    )
    client.post(
        "/v1/sandbox/create",
        json={"language": "python"},
        headers=auth_headers,
    )

    response = client.get("/v1/sandbox/list", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["sandboxes"]) == 2


def test_auth_required(client):
    # No auth header
    response = client.post(
        "/v1/sandbox/create",
        json={"language": "python"},
    )
    assert response.status_code in (401, 403, 422)


def test_auth_wrong_key(client):
    response = client.post(
        "/v1/sandbox/create",
        json={"language": "python"},
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code in (401, 403)
