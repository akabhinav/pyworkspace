import pytest
from fastapi.testclient import TestClient
from pymem.main import app, knowledge_store
from pymem.config import settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {settings.api_key}"}


@pytest.fixture(autouse=True)
def reset_store():
    """Reset the knowledge store before each test."""
    knowledge_store._documents.clear()
    knowledge_store._chunks.clear()
