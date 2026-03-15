"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from pyworkspace.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_ready(self, client):
        resp = await client.get("/ready")
        assert resp.status_code == 200

class TestWorkspaceEndpoints:
    @pytest.mark.asyncio
    async def test_create_workspace(self, client):
        resp = await client.post("/v1/workspaces", json={
            "name": "test-ws",
            "owner_id": "user-1",
            "org_id": "org-1",
            "tier": "standard",
            "services": [
                {"name": "postgres", "type": "postgres", "version": "16", "config": {"db": "testdb"}},
            ],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "test-ws"
        assert data["status"] == "provisioning"
        assert data["k8s_namespace"].startswith("pyws-")

    @pytest.mark.asyncio
    async def test_list_workspaces(self, client):
        resp = await client.get("/v1/workspaces")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_get_workspace_not_found(self, client):
        resp = await client.get("/v1/workspaces/nonexistent")
        assert resp.status_code == 404

class TestCatalogEndpoints:
    @pytest.mark.asyncio
    async def test_list_catalog(self, client):
        resp = await client.get("/v1/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        types = [s["type"] for s in data]
        assert "postgres" in types
        assert "redis" in types

    @pytest.mark.asyncio
    async def test_get_catalog_service(self, client):
        resp = await client.get("/v1/catalog/postgres")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "postgres"
        assert "agent_tools" in data

    @pytest.mark.asyncio
    async def test_get_catalog_not_found(self, client):
        resp = await client.get("/v1/catalog/nonexistent-service")
        assert resp.status_code == 404

class TestTemplateEndpoints:
    @pytest.mark.asyncio
    async def test_list_templates(self, client):
        resp = await client.get("/v1/templates")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
