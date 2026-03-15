import pytest
from fastapi.testclient import TestClient

from pysandbox.config import settings
from pysandbox.main import app
from pysandbox.sandbox_manager import sandbox_manager


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {settings.api_key}"}


@pytest.fixture(autouse=True)
def clear_sandboxes():
    """Clear all sandboxes before each test."""
    sandbox_manager._sandboxes.clear()
    yield
    sandbox_manager._sandboxes.clear()
