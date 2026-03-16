import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.postgres import tables


class User(Base[tables.User]):
    table = tables.User

    @classmethod
    async def update_status(
        cls,
        session: AsyncSession,
        user_id: str,
        online: bool,
        last_seen_at: datetime.datetime | None,
    ) -> tables.User:
        user = await cls.one_or_none(session, user_id=user_id)
        if user is None:
            return await cls.create(
                session,
                {
                    "id": user_id,
                    "online": online,
                    "last_seen_at": last_seen_at,
                    "options": {},
                },
            )
        await cls.update(session=session, id=user_id, online=online, last_seen_at=last_seen_at)
        return await cls.one(session, Filter.eq("id", user_id))

    @classmethod
    async def one_or_none(
        cls,
        session: AsyncSession,
        user_id: str,
    ) -> tables.User | None:
        return (await session.execute(select(cls.table).where(cls.table.id == user_id))).scalar_one_or_none()
