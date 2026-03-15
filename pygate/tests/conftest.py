import pytest
from fastapi.testclient import TestClient

from pygate.main import app
from pygate.config import settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {settings.api_key}"}
