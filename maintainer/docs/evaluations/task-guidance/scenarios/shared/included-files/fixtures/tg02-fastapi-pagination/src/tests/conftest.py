import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def test_app():
    return TestClient(app)
