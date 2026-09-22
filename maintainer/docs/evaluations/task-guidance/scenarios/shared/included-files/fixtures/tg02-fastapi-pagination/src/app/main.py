from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.notes import router
from app.db import database


@asynccontextmanager
async def lifespan(app):
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/notes")
