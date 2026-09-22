import pytest
from notes_client.client import NotesClient


class Transport:
    def get(self, path, **kwargs):
        class Response:
            def json(self):
                return []
        return Response()


@pytest.fixture
def client():
    return NotesClient(Transport())
