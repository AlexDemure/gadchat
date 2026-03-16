from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.postgres import tables


class Role(Base[tables.Role]):
    table = tables.Role

    @classmethod
    async def ensure(
        cls,
        session: AsyncSession,
        name: str,
    ) -> tables.Role:
        row = (await session.execute(select(cls.table).where(cls.table.name == name))).scalar_one_or_none()
        if row is not None:
            return row

        return await cls.create(session, {"id": name, "name": name})
