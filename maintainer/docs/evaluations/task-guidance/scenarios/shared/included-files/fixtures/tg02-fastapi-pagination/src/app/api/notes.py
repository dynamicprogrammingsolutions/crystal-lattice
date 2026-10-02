from fastapi import APIRouter, HTTPException
from . import crud
from .models import NoteCreate

router = APIRouter()


@router.get("/")
async def read_all_notes():
    return await crud.get_all()


@router.get("/{note_id}/")
async def read_note(note_id: int):
    note = await crud.get(note_id)
    if note is None:
        raise HTTPException(status_code=404)
    return note


@router.post("/", status_code=201)
async def create_note(payload: NoteCreate):
    note_id = await crud.post(payload)
    return {"id": note_id, **payload.model_dump()}


@router.put("/{note_id}/")
async def update_note(note_id: int, payload: NoteCreate):
    return await crud.put(note_id, payload)


@router.delete("/{note_id}/")
async def delete_note(note_id: int):
    return await crud.delete(note_id)
