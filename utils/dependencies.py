from utils.locator import Locator
from database import SessionMaker
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncSession:
    async with SessionMaker() as db:
        yield db


def get_locator():
    return Locator()
