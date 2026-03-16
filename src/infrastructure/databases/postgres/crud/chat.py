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
    ) -> dict[str, typing.Any]:
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
                cls.table.id,
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
        items: list[dict[str, typing.Any]] = []
        has_more = len(rows) > limit
        for chat_id, position, notifications, row_activity_at in rows[:limit]:
            chat = await cls.one(session, Filter.eq("id", chat_id))
            last_message = await Message.latest(session, Filter.eq("chat_id", chat_id))
            members = await Member.users(session, chat_id=chat_id)
            items.append(
                {
                    "chat": chat,
                    "last_message": last_message,
                    "members": members,
                    "pin_position": position,
                    "unread_count": notifications,
                    "activity_at": row_activity_at,
                }
            )

        prev_cursor = None
        next_cursor = None
        if items:
            first = items[0]
            last = items[-1]
            prev_cursor = Cursor.encode(
                {
                    "position": first["pin_position"],
                    "activity_at": first["activity_at"].isoformat() if first["activity_at"] is not None else None,
                    "chat_id": first["chat"].id,
                }
            )
            next_cursor = Cursor.encode(
                {
                    "position": last["pin_position"],
                    "activity_at": last["activity_at"].isoformat() if last["activity_at"] is not None else None,
                    "chat_id": last["chat"].id,
                }
            )

        for item in items:
            item.pop("activity_at")

        return {
            "items": items,
            "has_more": has_more,
            "prev_cursor": prev_cursor,
            "next_cursor": next_cursor,
        }


class Member(Base[tables.Member]):
    table = tables.Member

    @classmethod
    async def user_ids(
        cls,
        session: AsyncSession,
        chat_id: str,
        shard_id: int | None = None,
    ) -> list[str]:
        rows = await session.execute(
            select(tables.User.external_id)
            .join(cls.table, cls.table.user_id == tables.User.id)
            .where(cls.table.chat_id == chat_id)
        )
        return list(rows.scalars())

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

    @classmethod
    async def user(
        cls,
        session: AsyncSession,
        chat_id: str,
        user_id: str,
    ) -> tables.Member | None:
        row = await session.execute(
            select(cls.table)
            .join(tables.User, tables.User.id == cls.table.user_id)
            .where(cls.table.chat_id == chat_id)
            .where(tables.User.external_id == user_id)
        )
        return row.scalar_one_or_none()

    @classmethod
    async def mark_read(
        cls,
        session: AsyncSession,
        chat_member_id: str,
        message_id: str,
        read: datetime.datetime,
        unread_count: int,
    ) -> None:
        await cls.update(
            session=session,
            id=chat_member_id,
            notifications=unread_count,
        )

    @classmethod
    async def increment_unread(
        cls,
        session: AsyncSession,
        chat_id: str,
        shard_id: int | None,
        excluded_chat_member_id: str,
    ) -> None:
        rows = (
            await session.execute(
                select(cls.table.id, cls.table.notifications)
                .where(cls.table.chat_id == chat_id)
                .where(cls.table.id != excluded_chat_member_id)
            )
        ).all()
        for member_id, notifications in rows:
            await cls.update(session=session, id=member_id, notifications=(notifications or 0) + 1)


def _message_relations() -> tuple[typing.Any, ...]:
    return (
        selectinload(tables.Message.member).selectinload(tables.Member.user),
        selectinload(tables.Message.user),
        selectinload(tables.Message.attachments).selectinload(tables.Attachment.file),
        selectinload(tables.Message.reply).selectinload(tables.Reply.source_message).selectinload(tables.Message.member),
        selectinload(tables.Message.reply).selectinload(tables.Reply.source_message).selectinload(tables.Message.user),
        selectinload(tables.Message.forward)
        .selectinload(tables.Forward.source_message)
        .selectinload(tables.Message.member),
        selectinload(tables.Message.forward)
        .selectinload(tables.Forward.source_message)
        .selectinload(tables.Message.user),
    )


    @classmethod
    async def pin(
        cls,
        session: AsyncSession,
        member_id: str,
        user_id: str,
    ) -> None:
        rows = (
            await session.execute(
                select(cls.table.id, cls.table.position)
                .join(tables.User, tables.User.id == cls.table.user_id)
                .where(tables.User.external_id == user_id)
                .where(cls.table.position.is_not(None))
            )
        ).all()
        for row_member_id, position in rows:
            await cls.update(session=session, id=row_member_id, position=int(position) + 1)
        await cls.update(session=session, id=member_id, position=0)

    @classmethod
    async def unpin(
        cls,
        session: AsyncSession,
        member_id: str,
        user_id: str,
    ) -> None:
        row = (await session.execute(select(cls.table.id, cls.table.position).where(cls.table.id == member_id))).one_or_none()
        if row is None or row[1] is None:
            return
        position = int(row[1])
        rows = (
            await session.execute(
                select(cls.table.id, cls.table.position)
                .join(tables.User, tables.User.id == cls.table.user_id)
                .where(tables.User.external_id == user_id)
                .where(cls.table.position.is_not(None))
                .where(cls.table.position > position)
            )
        ).all()
        for row_member_id, member_position in rows:
            await cls.update(session=session, id=row_member_id, position=int(member_position) - 1)
        await cls.update(session=session, id=member_id, position=None)

    @classmethod
    async def reorder(
        cls,
        session: AsyncSession,
        user_id: str,
        chat_ids: list[str],
    ) -> None:
        rows = (
            await session.execute(
                select(cls.table.id, cls.table.chat_id)
                .join(tables.User, tables.User.id == cls.table.user_id)
                .where(tables.User.external_id == user_id)
            )
        ).all()
        by_chat = {chat_id: member_id for member_id, chat_id in rows}
        for member_id, _chat_id in rows:
            await cls.update(session=session, id=member_id, position=None)
        for index, chat_id in enumerate(chat_ids):
            if chat_id in by_chat:
                await cls.update(session=session, id=by_chat[chat_id], position=index)


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
    ) -> dict[str, typing.Any]:
        chat_id = filters.get("chat_id")
        text = filters.get("text")
        limit = pagination.get("limit")
        cursor = pagination.get("cursor")
        direction = getattr(sorting.get("direction"), "value", sorting.get("direction"))

        read_exists = exists(
            select(1)
            .select_from(tables.Read)
            .join(tables.Member, tables.Member.id == tables.Read.member_id)
            .where(tables.Read.message_id == cls.table.id)
            .where(or_(cls.table.member_id.is_(None), tables.Read.member_id != cls.table.member_id))
        )
        pin_rank = case((cls.table.pinned.is_(None), 1), else_=0)
        unpinned_created = case((cls.table.pinned.is_(None), cls.table.created), else_=None)
        statement = (
            select(cls.table, read_exists.label("is_read"))
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
        items = [{"message": message, "is_read": bool(is_read)} for message, is_read in rows[:limit]]
        prev_cursor = None
        next_cursor = None
        if items:
            first = items[0]["message"]
            last = items[-1]["message"]
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
        message_id: str,
        chat_id: str,
    ) -> None:
        await cls.update(
            session=session,
            id=message_id,
            chat_id=chat_id,
            pinned=datetime.datetime.now(datetime.timezone.utc),
        )

    @classmethod
    async def unpin(
        cls,
        session: AsyncSession,
        message_id: str,
        chat_id: str,
    ) -> None:
        await cls.update(session=session, id=message_id, chat_id=chat_id, pinned=None)


class Attachment(Base[tables.Attachment]):
    table = tables.Attachment

    @classmethod
    async def exists_in_chat(
        cls,
        session: AsyncSession,
        chat_id: str,
        file_id: str,
    ) -> bool:
        statement = (
            select(1)
            .select_from(cls.table)
            .join(tables.Message, tables.Message.id == cls.table.message_id)
            .where(cls.table.file_id == file_id)
            .where(tables.Message.chat_id == chat_id)
            .limit(1)
        )
        return (await session.execute(statement)).scalar_one_or_none() is not None


class Read(Base[tables.Read]):
    table = tables.Read

    @classmethod
    async def mark(
        cls,
        session: AsyncSession,
        chat_member: tables.Member,
        message: tables.Message,
        read: datetime.datetime,
    ) -> int:
        candidate_ids = (
            await session.execute(
                select(tables.Message.id)
                .where(tables.Message.chat_id == message.chat_id)
                .where(tables.Message.created <= message.created)
                .where(or_(tables.Message.member_id.is_(None), tables.Message.member_id != chat_member.id))
            )
        ).scalars().all()
        created_count = 0
        for message_id in candidate_ids:
            exists_statement = select(cls.table.id).where(cls.table.message_id == message_id).where(
                cls.table.member_id == chat_member.id
            )
            if (await session.execute(exists_statement)).scalar_one_or_none() is not None:
                continue
            await cls.create(
                session,
                {
                    "id": f"{chat_member.id}:{message_id}",
                    "message_id": message_id,
                    "member_id": chat_member.id,
                    "created": read,
                },
            )
            created_count += 1
        return created_count


class Reply(Base[tables.Reply]):
    table = tables.Reply


class Forward(Base[tables.Forward]):
    table = tables.Forward
