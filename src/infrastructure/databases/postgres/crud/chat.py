from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.databases.orm.sqlalchemy import models
from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.postgres import tables


class Chat(Base[tables.Chat]):
    table = tables.Chat

    @classmethod
    async def direct(
        cls,
        session: AsyncSession,
        user_a: str,
        user_b: str,
    ) -> tables.Chat | None:
        members = sorted([user_a, user_b])
        existing = await session.execute(
            select(cls.table)
            .join(tables.Member, tables.Member.chat_id == cls.table.id)
            .where(cls.table.kind == "direct")
            .where(tables.Member.user_id.in_(members))
            .group_by(cls.table.id)
            .having(func.count(tables.Member.user_id) == 2)
        )
        return existing.scalar_one_or_none()


class Member(Base[tables.Member]):
    table = tables.Member

    @classmethod
    async def ids(
        cls,
        session: AsyncSession,
        *filters: models.Filter | models.And | models.Or,
    ) -> list[str]:
        statement = cls.build(select(cls.table.user_id), filters=list(filters))
        rows = await session.execute(statement)
        return list(rows.scalars())

    @classmethod
    async def user(
        cls,
        session: AsyncSession,
        *filters: models.Filter | models.And | models.Or,
    ) -> tables.Member | None:
        statement = cls.build(select(cls.table), filters=list(filters))
        row = await session.execute(statement)
        return row.scalar_one_or_none()


class Message(Base[tables.Message]):
    table = tables.Message

    @classmethod
    async def duplicate(
        cls,
        session: AsyncSession,
        *filters: models.Filter | models.And | models.Or,
    ) -> tables.Message | None:
        statement = cls.build(
            select(cls.table).options(
                selectinload(cls.table.member),
                selectinload(cls.table.attachments).selectinload(tables.MessageFile.file),
            ),
            filters=list(filters),
        )
        dedup = await session.execute(statement)
        return dedup.scalar_one_or_none()

    @classmethod
    async def relations(
        cls,
        session: AsyncSession,
        *filters: models.Filter | models.And | models.Or,
    ) -> tables.Message:
        statement = cls.build(
            select(cls.table).options(
                selectinload(cls.table.member),
                selectinload(cls.table.attachments).selectinload(tables.MessageFile.file),
            ),
            filters=list(filters),
        )
        relation = await session.execute(statement)
        return relation.scalar_one()


class MessageFile(Base[tables.MessageFile]):
    table = tables.MessageFile
