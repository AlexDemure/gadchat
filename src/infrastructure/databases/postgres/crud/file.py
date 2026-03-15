from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.postgres import tables


class File(Base[tables.File]):
    table = tables.File

    @classmethod
    async def by_storage_key(
        cls,
        session: AsyncSession,
        bucket: str,
        key: str,
    ) -> tables.File | None:
        row = await session.execute(
            select(cls.table).where(
                cls.table.bucket == bucket,
                cls.table.key == key,
            )
        )
        return row.scalar_one_or_none()
