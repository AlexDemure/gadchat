import collections.abc

from fastapi import Header
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.databases.postgres import postgres


async def read() -> collections.abc.AsyncGenerator[AsyncSession, None]:
    async with postgres.orm.read() as session:
        yield session


async def write() -> collections.abc.AsyncGenerator[AsyncSession, None]:
    async with postgres.orm.write() as session:
        yield session


async def user_id(x_user_id: str | None = Header(default=None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return x_user_id


__all__ = [
    "AsyncSession",
    "HTTPException",
    "Header",
    "postgres",
]
