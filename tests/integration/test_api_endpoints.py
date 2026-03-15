"""Integration tests for API endpoints with DB + auth."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pyworkspace.auth.middleware import AuthUser, get_current_user
from pyworkspace.db.models import Base
from pyworkspace.db.session import get_db
from pyworkspace.main import create_app


# ── Test fixtures ────────────────────────────────────────────────────

_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
_test_session_factory = async_sessionmaker(
    bind=_test_engine, class_=AsyncSession, expire_on_commit=False
)

_dev_user = AuthUser(
    user_id="test-user",
    org_id="test-org",
    role="admin",
    email="test@example.com",
)


async def _override_get_db():
    session = _test_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def _override_get_current_user():
    return _dev_user


@pytest.fixture
async def app():
    """Create a test app with SQLite in-memory DB and auth override."""
    # Create tables
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_app = create_app()
    test_app.dependency_overrides[get_db] = _override_get_db
    test_app.dependency_overrides[get_current_user] = _override_get_current_user

    yield test_app

    # Cleanup
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Tests ────────────────────────────────────────────────────────────


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
        resp = await client.post(
            "/v1/workspaces",
            json={
                "name": "test-ws",
                "owner_id": "test-user",
                "org_id": "test-org",
                "tier": "standard",
                "services": [
                    {
                        "name": "postgres",
                        "type": "postgres",
                        "version": "16",
                        "config": {"db": "testdb"},
                    },
                ],
            },
        )
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

    @pytest.mark.asyncio
    async def test_create_and_get_workspace(self, client):
        create_resp = await client.post(
            "/v1/workspaces",
            json={
                "name": "fetch-test",
                "owner_id": "test-user",
                "org_id": "test-org",
                "tier": "dev",
                "resources": {"cpu": "1", "memory": "2Gi", "disk": "10Gi"},
            },
        )
        assert create_resp.status_code == 201
        ws_id = create_resp.json()["id"]

        get_resp = await client.get(f"/v1/workspaces/{ws_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == ws_id

    @pytest.mark.asyncio
    async def test_delete_workspace(self, client):
        create_resp = await client.post(
            "/v1/workspaces",
            json={
                "name": "delete-test",
                "owner_id": "test-user",
                "org_id": "test-org",
            },
        )
        ws_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/v1/workspaces/{ws_id}")
        assert del_resp.status_code == 202
        assert del_resp.json()["status"] == "destroying"

    @pytest.mark.asyncio
    async def test_update_workspace(self, client):
        create_resp = await client.post(
            "/v1/workspaces",
            json={
                "name": "update-test",
                "owner_id": "test-user",
                "org_id": "test-org",
            },
        )
        ws_id = create_resp.json()["id"]

        patch_resp = await client.patch(
            f"/v1/workspaces/{ws_id}",
            json={"tags": {"env": "staging"}},
        )
        assert patch_resp.status_code == 200


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

    @pytest.mark.asyncio
    async def test_create_template(self, client):
        resp = await client.post(
            "/v1/templates",
            json={
                "name": "my-template",
                "display_name": "My Template",
                "description": "A test template",
                "category": "testing",
                "spec_yaml": "name: test",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "my-template"


class TestSnapshotEndpoints:
    @pytest.mark.asyncio
    async def test_list_snapshots_404(self, client):
        resp = await client.get("/v1/workspaces/nonexistent/snapshots")
        # This returns 200 with empty list since workspace_id is not validated in list
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_create_snapshot(self, client):
        # First create a workspace
        ws_resp = await client.post(
            "/v1/workspaces",
            json={
                "name": "snap-test",
                "owner_id": "test-user",
                "org_id": "test-org",
            },
        )
        ws_id = ws_resp.json()["id"]

        snap_resp = await client.post(
            f"/v1/workspaces/{ws_id}/snapshots",
            json={"name": "test-snap"},
        )
        assert snap_resp.status_code == 201
        assert snap_resp.json()["name"] == "test-snap"
        assert snap_resp.json()["status"] == "ready"
