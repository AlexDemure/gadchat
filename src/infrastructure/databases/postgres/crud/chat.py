import typing
import datetime
import uuid

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

from .user import User


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
        membership = aliased(tables.ChatMember)
        chat_pin = aliased(tables.ChatPin)
        member = aliased(tables.Member)
        total_members = (
            select(func.count(tables.ChatMember.id))
            .where(tables.ChatMember.chat_id == cls.table.id)
            .correlate(cls.table)
            .scalar_subquery()
        )
        statement = (
            select(cls.table)
            .join(membership, membership.chat_id == cls.table.id)
            .join(member, member.id == membership.member_id)
            .where(cls.table.kind == "direct")
            .where(member.user_id.in_(members))
            .group_by(cls.table.id, cls.table.shard_id)
            .having(func.count(func.distinct(member.user_id)) == 2)
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
    ) -> dict[str, typing.Any]:
        user_id = filters.get("user_id")
        text = filters.get("text")
        limit = pagination.get("limit")
        cursor = pagination.get("cursor")
        direction = getattr(sorting.get("direction"), "value", sorting.get("direction"))

        membership = aliased(tables.ChatMember)
        member = aliased(tables.Member)

        latest_subquery = (
            select(
                tables.Message.chat_id,
                tables.Message.shard_id,
                func.max(tables.Message.created).label("latest_created"),
            )
            .group_by(tables.Message.chat_id, tables.Message.shard_id)
            .subquery()
        )
        activity_at = func.coalesce(latest_subquery.c.latest_created, cls.table.created)
        unread_count = (
            select(func.count(tables.Message.id))
            .where(tables.Message.chat_id == cls.table.id)
            .where(tables.Message.shard_id == cls.table.shard_id)
            .where(tables.Message.member_id != membership.member_id)
            .where(or_(membership.last_read_at.is_(None), tables.Message.created > membership.last_read_at))
            .correlate(cls.table, membership)
            .scalar_subquery()
        )
        pin_rank = case((chat_pin.position.is_(None), 1), else_=0)
        unpinned_activity_at = case((chat_pin.position.is_(None), activity_at), else_=None)

        statement = (
            select(
                cls.table.id,
                cls.table.shard_id,
                chat_pin.position,
                activity_at.label("activity_at"),
                unread_count.label("unread_count"),
            )
            .join(
                membership,
                and_(membership.chat_id == cls.table.id, membership.shard_id == cls.table.shard_id),
            )
            .outerjoin(chat_pin, chat_pin.chat_member_id == membership.id)
            .join(member, member.id == membership.member_id)
            .outerjoin(
                latest_subquery,
                and_(
                    latest_subquery.c.chat_id == cls.table.id,
                    latest_subquery.c.shard_id == cls.table.shard_id,
                ),
            )
            .outerjoin(
                tables.Message,
                and_(
                    tables.Message.chat_id == cls.table.id,
                    tables.Message.shard_id == cls.table.shard_id,
                    tables.Message.created == latest_subquery.c.latest_created,
                ),
            )
            .where(member.user_id == user_id)
        )

        if text:
            search = f"%{text}%"
            search_membership = aliased(tables.ChatMember)
            search_member = aliased(tables.Member)
            statement = statement.where(
                or_(
                    cls.table.title.ilike(search),
                    tables.Message.body.ilike(search),
                    exists(
                        select(1)
                        .select_from(search_membership)
                        .join(search_member, search_member.id == search_membership.member_id)
                        .where(search_membership.chat_id == cls.table.id)
                        .where(search_membership.shard_id == cls.table.shard_id)
                        .where(search_member.user_id.ilike(search))
                    ),
                )
            )

        if cursor is not None:
            cursor_payload = Cursor.decode(cursor)
            cursor_chat_id = uuid.UUID(cursor_payload["chat_id"])

            if cursor_payload.get("position") is not None:
                cursor_position = int(cursor_payload["position"])
                statement = statement.where(
                    or_(
                        chat_pin.position > cursor_position,
                        and_(chat_pin.position == cursor_position, cls.table.id > cursor_chat_id),
                        chat_pin.position.is_(None),
                    )
                )
            else:
                cursor_activity_at = datetime.datetime.fromisoformat(cursor_payload["activity_at"])
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
                statement = statement.where(chat_pin.position.is_(None), comparator)

        order = [
            pin_rank,
            chat_pin.position.asc().nullslast(),
            desc(unpinned_activity_at),
            desc(cls.table.id),
        ]
        if direction == "asc":
            order = [
                pin_rank,
                chat_pin.position.asc().nullslast(),
                unpinned_activity_at,
                cls.table.id,
            ]

        rows = (await session.execute(statement.order_by(*order).limit(limit + 1))).all()
        has_more = len(rows) > limit
        items = []
        members_by_chat: dict[tuple[uuid.UUID, int], list[dict[str, typing.Any]]] = {}
        for chat_id, chat_shard_id, position, row_activity_at, row_unread_count in rows[:limit]:
            chat = await cls.one(
                session,
                Filter.eq("id", chat_id),
                Filter.eq("shard_id", chat_shard_id),
            )
            last_message = await Message.latest(
                session,
                Filter.eq("chat_id", chat_id),
                Filter.eq("shard_id", chat_shard_id),
            )
            members = await ChatMember.users(session, chat_id=chat_id, shard_id=chat_shard_id)
            members_by_chat[(chat_id, chat_shard_id)] = members
            items.append((chat, last_message, row_activity_at, position, row_unread_count))

        prev_cursor = None
        next_cursor = None
        if items:
            prev_cursor = Cursor.encode(
                {
                    "position": items[0][3],
                    "activity_at": items[0][2].isoformat() if items[0][2] is not None else None,
                    "chat_id": str(items[0][0].id),
                }
            )
            next_cursor = Cursor.encode(
                {
                    "position": items[-1][3],
                    "activity_at": items[-1][2].isoformat() if items[-1][2] is not None else None,
                    "chat_id": str(items[-1][0].id),
                }
            )

        return {
            "items": [
                {
                    "chat": chat,
                    "last_message": last_message,
                    "members": members_by_chat[(chat.id, chat.shard_id)],
                    "pin_position": position,
                    "unread_count": unread_count_value,
                }
                for chat, last_message, _activity_at, position, unread_count_value in items
            ],
            "has_more": has_more,
            "prev_cursor": prev_cursor,
            "next_cursor": next_cursor,
        }


class Member(Base[tables.Member]):
    table = tables.Member

    @classmethod
    async def ensure(
        cls,
        session: AsyncSession,
        user_id: str,
        created: datetime.datetime,
    ) -> tables.Member:
        user = await User.one_or_none(session, user_id=user_id)
        if user is None:
            await User.create(
                session,
                {
                    "id": user_id,
                    "online": False,
                    "last_seen_at": None,
                    "options": {},
                },
            )

        row = (
            await session.execute(
                select(cls.table)
                .options(selectinload(cls.table.user))
                .where(cls.table.user_id == user_id)
            )
        ).scalar_one_or_none()
        if row is not None:
            return row

        return await cls.create(
            session,
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "created": created,
            },
        )

    @classmethod
    async def by_user_id(
        cls,
        session: AsyncSession,
        user_id: str,
    ) -> tables.Member | None:
        row = await session.execute(
            select(cls.table)
            .options(selectinload(cls.table.user))
            .where(cls.table.user_id == user_id)
        )
        return row.scalar_one_or_none()


class ChatMember(Base[tables.ChatMember]):
    table = tables.ChatMember

    @classmethod
    async def user_ids(
        cls,
        session: AsyncSession,
        chat_id: uuid.UUID,
        shard_id: int,
    ) -> list[str]:
        rows = await session.execute(
            select(tables.Member.user_id)
            .join(cls.table, cls.table.member_id == tables.Member.id)
            .where(cls.table.chat_id == chat_id)
            .where(cls.table.shard_id == shard_id)
        )
        return list(rows.scalars())

    @classmethod
    async def users(
        cls,
        session: AsyncSession,
        chat_id: uuid.UUID,
        shard_id: int,
    ) -> list[dict[str, typing.Any]]:
        rows = (
            await session.execute(
                select(tables.User.id, tables.User.online, tables.User.last_seen_at)
                .join(tables.Member, tables.Member.user_id == tables.User.id)
                .join(cls.table, cls.table.member_id == tables.Member.id)
                .where(cls.table.chat_id == chat_id)
                .where(cls.table.shard_id == shard_id)
            )
        ).all()
        return [
            {
                "user_id": user_id,
                "online": online,
                "last_seen_at": last_seen_at,
            }
            for user_id, online, last_seen_at in rows
        ]

    @classmethod
    async def user(
        cls,
        session: AsyncSession,
        chat_id: uuid.UUID,
        user_id: str,
    ) -> tables.ChatMember | None:
        row = await session.execute(
            select(cls.table)
            .join(tables.Member, tables.Member.id == cls.table.member_id)
            .where(cls.table.chat_id == chat_id)
            .where(tables.Member.user_id == user_id)
        )
        return row.scalar_one_or_none()

    @classmethod
    async def mark_read(
        cls,
        session: AsyncSession,
        chat_member_id: uuid.UUID,
        read_at: datetime.datetime,
    ) -> None:
        await cls.update(session=session, id=chat_member_id, last_read_at=read_at)


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
                selectinload(cls.table.member).selectinload(tables.Member.user),
                selectinload(cls.table.attachments).selectinload(tables.MessageFile.file),
            ),
            filters=list(filters),
        )
        return (await session.execute(statement)).scalar_one_or_none()

    @classmethod
    async def latest(
        cls,
        session: AsyncSession,
        *filters: models.Filter | models.And | models.Or,
    ) -> tables.Message | None:
        statement = cls.build(
            select(cls.table).options(selectinload(cls.table.member).selectinload(tables.Member.user)),
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
        statement = cls.build(
            select(cls.table).options(
                selectinload(cls.table.member).selectinload(tables.Member.user),
                selectinload(cls.table.attachments).selectinload(tables.MessageFile.file),
            ),
            filters=list(filters),
        )
        return (await session.execute(statement)).scalar_one()

    @classmethod
    async def search(
        cls,
        session: AsyncSession,
        filters: dict[str, typing.Any],
        sorting: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> dict[str, typing.Any]:
        chat_id = filters.get("chat_id")
        shard_id = filters.get("shard_id")
        text = filters.get("text")
        limit = pagination.get("limit")
        cursor = pagination.get("cursor")
        direction = getattr(sorting.get("direction"), "value", sorting.get("direction"))

        read_exists = exists(
            select(1)
            .select_from(tables.MessageRead)
            .join(tables.ChatMember, tables.ChatMember.id == tables.MessageRead.chat_member_id)
            .where(tables.MessageRead.message_id == cls.table.id)
            .where(tables.MessageRead.chat_id == cls.table.chat_id)
            .where(tables.ChatMember.member_id != cls.table.member_id)
        )
        pin_rank = case((cls.table.pinned_at.is_(None), 1), else_=0)
        unpinned_created = case((cls.table.pinned_at.is_(None), cls.table.created), else_=None)
        pinned_message_id = case((cls.table.pinned_at.is_not(None), cls.table.id), else_=None)
        unpinned_message_id = case((cls.table.pinned_at.is_(None), cls.table.id), else_=None)

        statement = (
            select(cls.table, read_exists.label("is_read"))
            .options(
                selectinload(cls.table.member).selectinload(tables.Member.user),
                selectinload(cls.table.attachments).selectinload(tables.MessageFile.file),
            )
            .where(cls.table.chat_id == chat_id)
            .where(cls.table.shard_id == shard_id)
        )

        if text:
            statement = statement.where(cls.table.body.like(f"%{text}%"))

        if cursor is not None:
            cursor_payload = Cursor.decode(cursor)
            cursor_message_id = uuid.UUID(cursor_payload["message_id"])
            if cursor_payload.get("pinned_at") is not None:
                cursor_pinned_at = datetime.datetime.fromisoformat(cursor_payload["pinned_at"])
                statement = statement.where(
                    or_(
                        cls.table.pinned_at < cursor_pinned_at,
                        and_(cls.table.pinned_at == cursor_pinned_at, cls.table.id < cursor_message_id),
                        cls.table.pinned_at.is_(None),
                    )
                )
            else:
                cursor_created = datetime.datetime.fromisoformat(cursor_payload["created"])
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
                statement = statement.where(cls.table.pinned_at.is_(None), comparator)

        order = [
            pin_rank,
            desc(cls.table.pinned_at),
            desc(pinned_message_id),
            desc(unpinned_created),
            desc(unpinned_message_id),
        ]
        if direction == "asc":
            order = [
                pin_rank,
                desc(cls.table.pinned_at),
                desc(pinned_message_id),
                unpinned_created,
                unpinned_message_id,
            ]

        rows = (await session.execute(statement.order_by(*order).limit(limit + 1))).all()
        has_more = len(rows) > limit
        sliced = rows[:limit]
        items = [{"message": message, "is_read": bool(is_read)} for message, is_read in sliced]

        prev_cursor = None
        next_cursor = None
        if items:
            first = items[0]["message"]
            last = items[-1]["message"]
            prev_cursor = Cursor.encode(
                {
                    "pinned_at": first.pinned_at.isoformat() if first.pinned_at is not None else None,
                    "created": first.created.isoformat(),
                    "message_id": str(first.id),
                }
            )
            next_cursor = Cursor.encode(
                {
                    "pinned_at": last.pinned_at.isoformat() if last.pinned_at is not None else None,
                    "created": last.created.isoformat(),
                    "message_id": str(last.id),
                }
            )

        return {
            "items": items,
            "has_more": has_more,
            "prev_cursor": prev_cursor,
            "next_cursor": next_cursor,
        }

    @classmethod
    async def pin(
        cls,
        session: AsyncSession,
        message_id: uuid.UUID,
        chat_id: uuid.UUID,
    ) -> None:
        await cls.update(
            session=session,
            id=message_id,
            chat_id=chat_id,
            pinned_at=datetime.datetime.now(datetime.timezone.utc),
        )

    @classmethod
    async def unpin(
        cls,
        session: AsyncSession,
        message_id: uuid.UUID,
        chat_id: uuid.UUID,
    ) -> None:
        await cls.update(
            session=session,
            id=message_id,
            chat_id=chat_id,
            pinned_at=None,
        )


class MessageFile(Base[tables.MessageFile]):
    table = tables.MessageFile


class ChatPin(Base[tables.ChatPin]):
    table = tables.ChatPin

    @classmethod
    async def chat_member(
        cls,
        session: AsyncSession,
        chat_member_id: uuid.UUID,
    ) -> tables.ChatPin | None:
        row = await session.execute(select(cls.table).where(cls.table.chat_member_id == chat_member_id))
        return row.scalar_one_or_none()

    @classmethod
    async def pin(
        cls,
        session: AsyncSession,
        chat_member_id: uuid.UUID,
        user_id: str,
    ) -> None:
        existing = await cls.chat_member(session, chat_member_id=chat_member_id)
        rows = list(
            (
                await session.execute(
                    select(cls.table)
                    .join(tables.ChatMember, tables.ChatMember.id == cls.table.chat_member_id)
                    .join(tables.Member, tables.Member.id == tables.ChatMember.member_id)
                    .where(tables.Member.user_id == user_id)
                    .where(cls.table.chat_member_id != chat_member_id)
                    .order_by(cls.table.position.asc(), cls.table.id.asc())
                )
            ).scalars()
        )

        if existing is None:
            existing = await cls.create(
                session,
                {
                    "id": uuid.uuid4(),
                    "chat_member_id": chat_member_id,
                    "position": 0,
                    "created": datetime.datetime.now(datetime.timezone.utc),
                },
            )
        await cls.update(session=session, id=existing.id, position=0)
        for position, row in enumerate(rows, start=1):
            await cls.update(session=session, id=row.id, position=position)

    @classmethod
    async def unpin(
        cls,
        session: AsyncSession,
        chat_member_id: uuid.UUID,
        user_id: str,
    ) -> None:
        existing = await cls.chat_member(session, chat_member_id=chat_member_id)
        if existing is None:
            return

        rows = list(
            (
                await session.execute(
                    select(cls.table)
                    .join(tables.ChatMember, tables.ChatMember.id == cls.table.chat_member_id)
                    .join(tables.Member, tables.Member.id == tables.ChatMember.member_id)
                    .where(tables.Member.user_id == user_id)
                    .where(cls.table.position > existing.position)
                    .order_by(cls.table.position.asc(), cls.table.id.asc())
                )
            ).scalars()
        )
        for row in rows:
            await cls.update(session=session, id=row.id, position=row.position - 1)

        await cls.delete(session, Filter.eq("id", existing.id))

    @classmethod
    async def reorder(
        cls,
        session: AsyncSession,
        user_id: str,
        chat_ids: list[uuid.UUID],
    ) -> None:
        rows = (
            await session.execute(
                select(tables.ChatMember.chat_id, cls.table.id, cls.table.position)
                .join(tables.ChatMember, tables.ChatMember.id == cls.table.chat_member_id)
                .join(tables.Member, tables.Member.id == tables.ChatMember.member_id)
                .where(tables.Member.user_id == user_id)
            )
        ).all()
        pins_by_chat_id = {
            chat_id: {
                "pin_id": pin_id,
                "position": position,
            }
            for chat_id, pin_id, position in rows
        }
        ordered_chat_ids = list(dict.fromkeys(chat_id for chat_id in chat_ids if chat_id in pins_by_chat_id))
        tail_chat_ids = [
            chat_id
            for chat_id, payload in sorted(
                pins_by_chat_id.items(),
                key=lambda item: (item[1]["position"], str(item[0])),
            )
            if chat_id not in ordered_chat_ids
        ]
        for position, chat_id in enumerate([*ordered_chat_ids, *tail_chat_ids]):
            await cls.update(session=session, id=pins_by_chat_id[chat_id]["pin_id"], position=position)


class MessageRead(Base[tables.MessageRead]):
    table = tables.MessageRead

    @classmethod
    async def mark(
        cls,
        session: AsyncSession,
        chat_member: tables.ChatMember,
        message: tables.Message,
        read_at: datetime.datetime,
    ) -> int:
        statement = (
            select(tables.Message.id, tables.Message.chat_id)
            .where(tables.Message.chat_id == message.chat_id)
            .where(tables.Message.shard_id == message.shard_id)
            .where(tables.Message.member_id != chat_member.member_id)
            .where(tables.Message.created <= message.created)
        )
        if chat_member.last_read_at is not None:
            statement = statement.where(tables.Message.created > chat_member.last_read_at)

        statement = statement.where(
            ~exists(
                select(1)
                .select_from(cls.table)
                .where(cls.table.chat_member_id == chat_member.id)
                .where(cls.table.message_id == tables.Message.id)
                .where(cls.table.chat_id == tables.Message.chat_id)
            )
        )

        rows = (await session.execute(statement)).all()
        for message_id, chat_id in rows:
            session.add(
                cls.table(
                    id=uuid.uuid4(),
                    shard_id=chat_member.shard_id,
                    chat_id=chat_id,
                    message_id=message_id,
                    chat_member_id=chat_member.id,
                    read_at=read_at,
                )
            )
        await session.flush()
        return len(rows)
