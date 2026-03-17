import datetime
import typing

from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import with_loader_criteria

from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.orm.sqlalchemy.models import And
from src.infrastructure.databases.orm.sqlalchemy.models import Filter
from src.infrastructure.databases.orm.sqlalchemy.models import Or
from src.infrastructure.databases.orm.sqlalchemy.utils import fetchone
from src.infrastructure.databases.postgres import tables
from src.infrastructure.databases.postgres.pagination import Cursor


class Chat(Base[tables.Chat]):
    table = tables.Chat

    @classmethod
    async def relations(cls, session: AsyncSession, *filters: typing.Union[Filter, And, Or]) -> tables.Chat:
        statement = select(cls.table).options(
            selectinload(cls.table.members).selectinload(tables.Member.user),
            selectinload(cls.table.members).selectinload(tables.Member.role),
        )
        statement = cls.build(statement, filters=list(filters))
        return await fetchone(session, statement)

    @classmethod
    async def search(
        cls,
        session: AsyncSession,
        filters: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> tuple[list[tables.Chat], bool, str | None, str | None]:
        limit = pagination.get("limit")
        user_id = filters.get("user_id")

        async def _common() -> tuple[list[tables.Chat], bool, str | None, str | None]:
            statement = select(cls.table).options(
                selectinload(cls.table.members).selectinload(tables.Member.user),
                selectinload(cls.table.members).selectinload(tables.Member.role),
            )

            if cursor := pagination.get("cursor"):
                payload = Cursor.decode(cursor)
                chat_id = payload["chat_id"]
                created = datetime.datetime.fromisoformat(payload["created"])

                statement = statement.where(
                    or_(
                        cls.table.created < created,
                        and_(
                            cls.table.created == created,
                            cls.table.id < chat_id,
                        ),
                    )
                )

            statement = statement.order_by(desc(cls.table.created), desc(cls.table.id))

            rows = (await session.execute(statement.limit(limit + 1))).scalars().all()

            more = len(rows) > limit
            chats = rows[:limit]

            if chats:
                prev = Cursor.encode(
                    {
                        "created": chats[0].created.isoformat(),
                        "chat_id": chats[0].id,
                    }
                )
                next = Cursor.encode(
                    {
                        "created": chats[-1].created.isoformat(),
                        "chat_id": chats[-1].id,
                    }
                )
            else:
                prev = next = None

            return chats, more, prev, next

        async def _personal() -> tuple[list[tables.Chat], bool, str | None, str | None]:
            latest_subquery = (
                select(
                    tables.Message.chat_id,
                    func.max(tables.Message.created).label("latest_created"),
                )
                .group_by(tables.Message.chat_id)
                .subquery()
            )

            activity_at = func.coalesce(latest_subquery.c.latest_created, cls.table.created)

            statement = (
                select(
                    cls.table,
                    tables.Member.position,
                    activity_at.label("activity_at"),
                )
                .options(
                    selectinload(cls.table.members).selectinload(tables.Member.user),
                    selectinload(cls.table.members).selectinload(tables.Member.role),
                )
                .join(tables.Member, tables.Member.chat_id == cls.table.id)
                .outerjoin(latest_subquery, latest_subquery.c.chat_id == cls.table.id)
            )

            statement = statement.where(tables.Member.user_id == user_id)

            if cursor := pagination.get("cursor"):
                payload = Cursor.decode(cursor)
                chat_id = payload["chat_id"]
                position = payload["position"]
                cursor_activity_at = datetime.datetime.fromisoformat(payload["activity_at"])

                if position is not None:
                    statement = statement.where(
                        or_(
                            tables.Member.position.is_(None),
                            tables.Member.position > position,
                            and_(
                                tables.Member.position == position,
                                or_(
                                    activity_at < cursor_activity_at,
                                    and_(
                                        activity_at == cursor_activity_at,
                                        cls.table.id < chat_id,
                                    ),
                                ),
                            ),
                        )
                    )
                else:
                    statement = statement.where(tables.Member.position.is_(None))
                    statement = statement.where(
                        or_(
                            activity_at < cursor_activity_at,
                            and_(
                                activity_at == cursor_activity_at,
                                cls.table.id < chat_id,
                            ),
                        )
                    )

            statement = statement.order_by(
                tables.Member.position.asc().nullslast(),
                desc(activity_at),
                desc(cls.table.id),
            )

            rows = (await session.execute(statement.limit(limit + 1))).all()

            more = len(rows) > limit

            chats = [chat for chat, _position, _activity_at in rows[:limit]]

            if chats:
                first_chat, first_position, first_activity_at = rows[0]
                last_chat, last_position, last_activity_at = rows[min(limit, len(rows)) - 1]

                prev = Cursor.encode(
                    {
                        "position": first_position,
                        "activity_at": first_activity_at.isoformat(),
                        "chat_id": first_chat.id,
                    }
                )
                next = Cursor.encode(
                    {
                        "position": last_position,
                        "activity_at": last_activity_at.isoformat(),
                        "chat_id": last_chat.id,
                    }
                )
            else:
                prev = next = None

            return chats, more, prev, next

        if user_id is None:
            return await _common()
        else:
            return await _personal()


class Member(Base[tables.Member]):
    table = tables.Member


def _message_relations(member_id: str | None) -> tuple[typing.Any, ...]:
    relations: list[typing.Any] = [
        selectinload(tables.Message.reads),
        selectinload(tables.Message.member).selectinload(tables.Member.role),
        selectinload(tables.Message._attachments).selectinload(tables.Attachment.file),
        selectinload(tables.Message._reply)
        .selectinload(tables.Reply.source_message)
        .selectinload(tables.Message.member),
        selectinload(tables.Message._reply)
        .selectinload(tables.Reply.source_message)
        .selectinload(tables.Message.member)
        .selectinload(tables.Member.role),
        selectinload(tables.Message._reply)
        .selectinload(tables.Reply.source_message)
        .selectinload(tables.Message._attachments)
        .selectinload(tables.Attachment.file),
        selectinload(tables.Message._forward)
        .selectinload(tables.Forward.source_message)
        .selectinload(tables.Message.member),
        selectinload(tables.Message._forward)
        .selectinload(tables.Forward.source_message)
        .selectinload(tables.Message.member)
        .selectinload(tables.Member.role),
        selectinload(tables.Message._forward)
        .selectinload(tables.Forward.source_message)
        .selectinload(tables.Message._attachments)
        .selectinload(tables.Attachment.file),
    ]
    if member_id is not None:
        relations.append(with_loader_criteria(tables.Read, tables.Read.member_id == member_id, include_aliases=True))
    return tuple(relations)


class Message(Base[tables.Message]):
    table = tables.Message

    @classmethod
    async def search(
        cls,
        session: AsyncSession,
        filters: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> tuple[list[tables.Message], bool, str | None, str | None]:
        chat_id = filters.get("chat_id")
        text = filters.get("text")
        member_id = filters.get("member_id")
        limit = pagination.get("limit")
        cursor = pagination.get("cursor")
        statement = select(cls.table).options(*_message_relations(member_id)).where(cls.table.chat_id == chat_id)

        if text:
            statement = statement.where(cls.table.text.like(f"%{text}%"))

        if cursor is not None:
            payload = Cursor.decode(cursor)
            cursor_message_id = payload["message_id"]
            cursor_created = datetime.datetime.fromisoformat(payload["created"])
            statement = statement.where(
                or_(
                    cls.table.created < cursor_created,
                    and_(cls.table.created == cursor_created, cls.table.id < cursor_message_id),
                )
            )

        rows = (
            await session.execute(statement.order_by(desc(cls.table.created), desc(cls.table.id)).limit(limit + 1))
        ).all()
        has_more = len(rows) > limit
        items = [message for (message,) in rows[:limit]]
        prev_cursor = None
        next_cursor = None
        if items:
            first = items[0]
            last = items[-1]
            prev_cursor = Cursor.encode(
                {
                    "created": first.created.isoformat(),
                    "message_id": first.id,
                }
            )
            next_cursor = Cursor.encode(
                {
                    "created": last.created.isoformat(),
                    "message_id": last.id,
                }
            )
        return items, has_more, prev_cursor, next_cursor


class Attachment(Base[tables.Attachment]):
    table = tables.Attachment


class Read(Base[tables.Read]):
    table = tables.Read


class Reply(Base[tables.Reply]):
    table = tables.Reply


class Forward(Base[tables.Forward]):
    table = tables.Forward
