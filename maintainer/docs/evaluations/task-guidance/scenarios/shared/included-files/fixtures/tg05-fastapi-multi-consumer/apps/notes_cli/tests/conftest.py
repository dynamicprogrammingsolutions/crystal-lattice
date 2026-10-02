import pytest


class Client:
    def list_notes(self):
        return [{"id": 1, "title": "First"}]


@pytest.fixture
def client():
    return Client()
