import os
import httpx


class NotesClient:
    def __init__(self, transport):
        self.transport = transport

    @classmethod
    def from_environment(cls):
        return cls(
            httpx.Client(
                base_url=os.environ.get(
                    "NOTES_API_URL",
                    "http://127.0.0.1:8000",
                )
            )
        )

    def list_notes(self):
        return self.transport.get("/notes/").json()
