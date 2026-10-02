from pydantic import BaseModel


class NoteCreate(BaseModel):
    title: str
    description: str


class Note(NoteCreate):
    id: int
