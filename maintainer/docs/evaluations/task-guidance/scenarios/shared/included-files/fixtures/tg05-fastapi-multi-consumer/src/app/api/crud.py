from app.db import database, notes


async def get_all():
    return await database.fetch_all(notes.select())


async def get(note_id):
    return await database.fetch_one(notes.select().where(notes.c.id == note_id))


async def post(payload):
    return await database.execute(notes.insert().values(**payload.model_dump()))


async def put(note_id, payload):
    await database.execute(
        notes.update().where(notes.c.id == note_id).values(**payload.model_dump())
    )
    return await get(note_id)


async def delete(note_id):
    note = await get(note_id)
    await database.execute(notes.delete().where(notes.c.id == note_id))
    return note
