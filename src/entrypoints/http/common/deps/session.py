import collections.abc

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.databases.postgres import postgres


async def read() -> collections.abc.AsyncGenerator[AsyncSession, None]:
    async with postgres.orm.read() as session:
        yield session


async def write() -> collections.abc.AsyncGenerator[AsyncSession, None]:
    async with postgres.orm.write() as session:
        yield session
