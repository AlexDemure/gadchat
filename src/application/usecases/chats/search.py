import typing

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import exists
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select

from src.application.utils.chats import decode_chat_cursor
from src.application.utils.chats import encode_chat_cursor
from src.infrastructure.databases.orm.sqlalchemy import queries
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres.crud import Member
from src.infrastructure.databases.postgres.tables import Chat
from src.infrastructure.databases.postgres.tables import Message


class Repositories:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.member = Member


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repositories: Repositories, security: Security) -> None:
        self.repositories = repositories
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def __call__(
        self,
        user_id: str,
        limit: int,
        cursor: str | None,
        text: str | None,
    ) -> dict[str, typing.Any]:
        session = self.container.repositories.session

        latest_subquery = (
            select(
                Message.chat_id,
                Message.shard_id,
                func.max(Message.created).label("latest_created"),
            )
            .group_by(Message.chat_id, Message.shard_id)
            .subquery()
        )

        activity_at = func.coalesce(latest_subquery.c.latest_created, Chat.created)
        statement = (
            select(
                Chat.id,
                Chat.shard_id,
                Chat.kind,
                Chat.title,
                latest_subquery.c.latest_created,
                Message.body,
                activity_at.label("activity_at"),
            )
            .join(
                self.container.repositories.member.table,
                and_(
                    self.container.repositories.member.table.chat_id == Chat.id,
                    self.container.repositories.member.table.shard_id == Chat.shard_id,
                ),
            )
            .outerjoin(
                latest_subquery,
                and_(
                    latest_subquery.c.chat_id == Chat.id,
                    latest_subquery.c.shard_id == Chat.shard_id,
                ),
            )
            .outerjoin(
                Message,
                and_(
                    Message.chat_id == Chat.id,
                    Message.shard_id == Chat.shard_id,
                    Message.created == latest_subquery.c.latest_created,
                ),
            )
            .where(self.container.repositories.member.table.user_id == user_id)
        )

        if text:
            search = f"%{text}%"
            statement = statement.where(
                or_(
                    Chat.title.ilike(search),
                    Message.body.ilike(search),
                    exists(
                        select(1)
                        .select_from(Member.table)
                        .where(Member.table.chat_id == Chat.id)
                        .where(Member.table.shard_id == Chat.shard_id)
                        .where(Member.table.user_id.ilike(search))
                    ),
                )
            )

        if cursor:
            try:
                cursor_activity_at, cursor_chat_id = decode_chat_cursor(cursor)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid cursor") from exc

            statement = statement.where(
                or_(
                    activity_at < cursor_activity_at,
                    and_(
                        activity_at == cursor_activity_at,
                        Chat.id < cursor_chat_id,
                    ),
                )
            )

        rows = await session.execute(statement.order_by(desc(activity_at), desc(Chat.id)).limit(limit + 1))

        items = []
        raw_items = rows.all()
        has_more = len(raw_items) > limit
        raw_items = raw_items[:limit]
        for chat_id, chat_shard_id, _kind, _title, _latest_created, _body, _activity_at in raw_items:
            chat = await session.get(Chat, chat_id)
            if chat is None:
                continue
            last_message_row = await session.execute(
                select(Message)
                .where(
                    Message.chat_id == chat_id,
                    Message.shard_id == chat_shard_id,
                )
                .order_by(desc(Message.created), desc(Message.id))
                .limit(1)
            )
            last_message = last_message_row.scalar_one_or_none()
            members = await self.container.repositories.member.ids(
                session,
                queries.Filter.eq(key="chat_id", value=chat_id),
                queries.Filter.eq(key="shard_id", value=chat_shard_id),
            )
            items.append(
                {
                    "chat": chat,
                    "last_message": last_message,
                    "members": members,
                }
            )

        prev_cursor = None
        next_cursor = None
        if raw_items:
            first_activity_at = raw_items[0][6]
            last_activity_at = raw_items[-1][6]
            if first_activity_at is not None:
                prev_cursor = encode_chat_cursor(first_activity_at, raw_items[0][0])
            if last_activity_at is not None:
                next_cursor = encode_chat_cursor(last_activity_at, raw_items[-1][0])

        return {
            "items": items,
            "has_more": has_more,
            "prev_cursor": prev_cursor,
            "next_cursor": next_cursor,
        }
