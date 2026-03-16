import datetime
import typing

from sqlalchemy import and_
from sqlalchemy import case
from sqlalchemy import desc
from sqlalchemy import exists
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.orm import selectinload

from src.infrastructure.databases.orm.sqlalchemy import models
from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.queries import Pagination
from src.infrastructure.databases.orm.sqlalchemy.queries import Sorting
from src.infrastructure.databases.postgres import tables
from src.infrastructure.databases.postgres.pagination import Cursor


class Chat(Base[tables.Chat]):
    table = tables.Chat

    @classmethod
    async def direct(
        cls,
        session: AsyncSession,
        user_a: str,
        user_b: str,
    ) -> tables.Chat | None:
        member = aliased(tables.Member)
        user = aliased(tables.User)
        total_members = (
            select(func.count(tables.Member.id))
            .where(tables.Member.chat_id == cls.table.id)
            .correlate(cls.table)
            .scalar_subquery()
        )
        statement = (
            select(cls.table)
            .join(member, member.chat_id == cls.table.id)
            .join(user, user.id == member.user_id)
            .where(user.external_id.in_([user_a, user_b]))
            .group_by(cls.table.id)
            .having(func.count(func.distinct(user.external_id)) == 2)
            .having(total_members == 2)
        )
        return (await session.execute(statement)).scalar_one_or_none()

    @classmethod
    async def search(
        cls,
        session: AsyncSession,
        filters: dict[str, typing.Any],
        sorting: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> tuple[list[tables.Chat], bool, str | None, str | None]:
        user_id = filters.get("user_id")
        text = filters.get("text")
        limit = pagination.get("limit")
        cursor = pagination.get("cursor")
        direction = getattr(sorting.get("direction"), "value", sorting.get("direction"))

        membership = aliased(tables.Member)
        user = aliased(tables.User)
        latest_subquery = (
            select(
                tables.Message.chat_id,
                func.max(tables.Message.created).label("latest_created"),
            )
            .group_by(tables.Message.chat_id)
            .subquery()
        )
        latest_message = aliased(tables.Message)
        activity_at = func.coalesce(latest_subquery.c.latest_created, cls.table.created)
        position_rank = case((membership.position.is_(None), 1), else_=0)
        unpinned_activity_at = case((membership.position.is_(None), activity_at), else_=None)
        statement = (
            select(
                cls.table,
                membership.position,
                membership.notifications,
                activity_at.label("activity_at"),
            )
            .join(membership, membership.chat_id == cls.table.id)
            .join(user, user.id == membership.user_id)
            .outerjoin(latest_subquery, latest_subquery.c.chat_id == cls.table.id)
            .outerjoin(
                latest_message,
                and_(
                    latest_message.chat_id == cls.table.id,
                    latest_message.created == latest_subquery.c.latest_created,
                ),
            )
            .where(user.external_id == user_id)
        )

        if text:
            search = f"%{text}%"
            member_search = aliased(tables.Member)
            user_search = aliased(tables.User)
            statement = statement.where(
                or_(
                    cls.table.title.ilike(search),
                    exists(
                        select(1)
                        .select_from(tables.Message)
                        .where(tables.Message.chat_id == cls.table.id)
                        .where(tables.Message.text.ilike(search))
                    ),
                    exists(
                        select(1)
                        .select_from(member_search)
                        .join(user_search, user_search.id == member_search.user_id)
                        .where(member_search.chat_id == cls.table.id)
                        .where(user_search.external_id.ilike(search))
                    ),
                )
            )

        if cursor is not None:
            payload = Cursor.decode(cursor)
            cursor_chat_id = payload["chat_id"]
            if payload.get("position") is not None:
                cursor_position = int(payload["position"])
                statement = statement.where(
                    or_(
                        membership.position > cursor_position,
                        and_(membership.position == cursor_position, cls.table.id > cursor_chat_id),
                        membership.position.is_(None),
                    )
                )
            else:
                cursor_activity_at = datetime.datetime.fromisoformat(payload["activity_at"])
                comparator = (
                    or_(
                        activity_at < cursor_activity_at,
                        and_(activity_at == cursor_activity_at, cls.table.id < cursor_chat_id),
                    )
                    if direction == "desc"
                    else or_(
                        activity_at > cursor_activity_at,
                        and_(activity_at == cursor_activity_at, cls.table.id > cursor_chat_id),
                    )
                )
                statement = statement.where(membership.position.is_(None), comparator)

        order = [
            position_rank,
            membership.position.asc().nullslast(),
            desc(unpinned_activity_at),
            desc(cls.table.id),
        ]
        if direction == "asc":
            order = [
                position_rank,
                membership.position.asc().nullslast(),
                unpinned_activity_at,
                cls.table.id,
            ]

        rows = (await session.execute(statement.order_by(*order).limit(limit + 1))).all()
        has_more = len(rows) > limit
        items = [chat for chat, _position, _notifications, _activity_at in rows[:limit]]

        prev_cursor = None
        next_cursor = None
        if rows[:limit]:
            first_chat, first_position, _first_notifications, first_activity_at = rows[0]
            last_chat, last_position, _last_notifications, last_activity_at = rows[min(limit, len(rows)) - 1]
            prev_cursor = Cursor.encode(
                {
                    "position": first_position,
                    "activity_at": first_activity_at.isoformat() if first_activity_at is not None else None,
                    "chat_id": first_chat.id,
                }
            )
            next_cursor = Cursor.encode(
                {
                    "position": last_position,
                    "activity_at": last_activity_at.isoformat() if last_activity_at is not None else None,
                    "chat_id": last_chat.id,
                }
            )

        return items, has_more, prev_cursor, next_cursor


class Member(Base[tables.Member]):
    table = tables.Member

    @classmethod
    async def users(
        cls,
        session: AsyncSession,
        chat_id: str,
        shard_id: int | None = None,
    ) -> list[dict[str, typing.Any]]:
        rows = (
            await session.execute(
                select(tables.User.external_id, tables.Role.name)
                .join(cls.table, cls.table.user_id == tables.User.id)
                .join(tables.Role, tables.Role.id == cls.table.role_id)
                .where(cls.table.chat_id == chat_id)
            )
        ).all()
        return [{"user_id": user_id, "role": role} for user_id, role in rows]


def _message_relations() -> tuple[typing.Any, ...]:
    return (
        selectinload(tables.Message.member).selectinload(tables.Member.user),
        selectinload(tables.Message.user),
        selectinload(tables.Message.attachments).selectinload(tables.Attachment.file),
        selectinload(tables.Message.reply)
        .selectinload(tables.Reply.source_message)
        .selectinload(tables.Message.member),
        selectinload(tables.Message.reply).selectinload(tables.Reply.source_message).selectinload(tables.Message.user),
        selectinload(tables.Message.forward)
        .selectinload(tables.Forward.source_message)
        .selectinload(tables.Message.member),
        selectinload(tables.Message.forward)
        .selectinload(tables.Forward.source_message)
        .selectinload(tables.Message.user),
    )


class Message(Base[tables.Message]):
    table = tables.Message

    @classmethod
    async def duplicate(
        cls,
        session: AsyncSession,
        *filters: models.Filter | models.And | models.Or,
    ) -> tables.Message | None:
        statement = cls.build(select(cls.table).options(*_message_relations()), filters=list(filters))
        return (await session.execute(statement)).scalar_one_or_none()

    @classmethod
    async def latest(
        cls,
        session: AsyncSession,
        *filters: models.Filter | models.And | models.Or,
    ) -> tables.Message | None:
        statement = cls.build(
            select(cls.table).options(*_message_relations()),
            filters=list(filters),
            sorting=[Sorting.desc("created"), Sorting.desc("id")],
            pagination=Pagination.page(1),
        )
        return (await session.execute(statement)).scalar_one_or_none()

    @classmethod
    async def relations(
        cls,
        session: AsyncSession,
        *filters: models.Filter | models.And | models.Or,
    ) -> tables.Message:
        statement = cls.build(select(cls.table).options(*_message_relations()), filters=list(filters))
        return (await session.execute(statement)).scalar_one()

    @classmethod
    async def search(
        cls,
        session: AsyncSession,
        filters: dict[str, typing.Any],
        sorting: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> tuple[list[tables.Message], bool, str | None, str | None]:
        chat_id = filters.get("chat_id")
        text = filters.get("text")
        limit = pagination.get("limit")
        cursor = pagination.get("cursor")
        direction = getattr(sorting.get("direction"), "value", sorting.get("direction"))

        pin_rank = case((cls.table.pinned.is_(None), 1), else_=0)
        unpinned_created = case((cls.table.pinned.is_(None), cls.table.created), else_=None)
        statement = (
            select(cls.table)
            .options(*_message_relations())
            .where(cls.table.chat_id == chat_id)
        )

        if text:
            statement = statement.where(cls.table.text.like(f"%{text}%"))

        if cursor is not None:
            payload = Cursor.decode(cursor)
            cursor_message_id = payload["message_id"]
            if payload.get("pinned") is not None:
                cursor_pinned = datetime.datetime.fromisoformat(payload["pinned"])
                statement = statement.where(
                    or_(
                        cls.table.pinned < cursor_pinned,
                        and_(cls.table.pinned == cursor_pinned, cls.table.id < cursor_message_id),
                        cls.table.pinned.is_(None),
                    )
                )
            else:
                cursor_created = datetime.datetime.fromisoformat(payload["created"])
                comparator = (
                    or_(
                        cls.table.created < cursor_created,
                        and_(cls.table.created == cursor_created, cls.table.id < cursor_message_id),
                    )
                    if direction == "desc"
                    else or_(
                        cls.table.created > cursor_created,
                        and_(cls.table.created == cursor_created, cls.table.id > cursor_message_id),
                    )
                )
                statement = statement.where(cls.table.pinned.is_(None), comparator)

        order = [
            pin_rank,
            desc(cls.table.pinned),
            desc(cls.table.created),
            desc(cls.table.id),
        ]
        if direction == "asc":
            order = [
                pin_rank,
                desc(cls.table.pinned),
                cls.table.created,
                cls.table.id,
            ]

        rows = (await session.execute(statement.order_by(*order).limit(limit + 1))).all()
        has_more = len(rows) > limit
        items = [message for message, in rows[:limit]]
        prev_cursor = None
        next_cursor = None
        if items:
            first = items[0]
            last = items[-1]
            prev_cursor = Cursor.encode(
                {
                    "pinned": first.pinned.isoformat() if first.pinned is not None else None,
                    "created": first.created.isoformat(),
                    "message_id": first.id,
                }
            )
            next_cursor = Cursor.encode(
                {
                    "pinned": last.pinned.isoformat() if last.pinned is not None else None,
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
