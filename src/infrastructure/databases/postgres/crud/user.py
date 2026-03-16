import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.postgres import tables


class User(Base[tables.User]):
    table = tables.User

    @classmethod
    async def by_external_id(
        cls,
        session: AsyncSession,
        external_id: str,
    ) -> tables.User | None:
        return (
            await session.execute(select(cls.table).where(cls.table.external_id == external_id))
        ).scalar_one_or_none()

    @classmethod
    async def ensure(
        cls,
        session: AsyncSession,
        external_id: str,
    ) -> tables.User:
        if row := await cls.by_external_id(session, external_id=external_id):
            return row
        return await cls.create(
            session,
            {
                "id": str(uuid.uuid4()),
                "external_id": external_id,
                "authorization": None,
                "options": {},
            },
        )
