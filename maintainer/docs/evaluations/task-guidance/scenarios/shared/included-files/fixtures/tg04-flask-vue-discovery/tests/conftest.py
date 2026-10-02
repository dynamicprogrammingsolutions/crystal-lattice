import pytest
from server.app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()
