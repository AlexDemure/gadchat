import typing
import uuid

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.application.utils.chats.message import decode_message_cursor
from src.application.utils.chats.message import encode_message_cursor
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres.tables import Member
from src.infrastructure.databases.postgres.tables import Message
from src.infrastructure.databases.postgres.tables import MessageFile


class Repositories:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.member = Member
        self.message = Message


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
        *,
        chat_id: uuid.UUID,
        user_id: str,
        cursor: str | None,
        direction: str,
        limit: int,
    ) -> dict[str, typing.Any]:
        session = self.container.repositories.session

        membership = await session.execute(
            select(self.container.repositories.member).where(
                self.container.repositories.member.chat_id == chat_id,
                self.container.repositories.member.user_id == user_id,
            )
        )
        if membership.scalar_one_or_none() is None:
            raise HTTPException(status_code=403, detail="User is not a member of the chat")

        query = (
            select(self.container.repositories.message)
            .options(
                selectinload(self.container.repositories.message.member),
                selectinload(self.container.repositories.message.attachments).selectinload(MessageFile.file),
            )
            .where(self.container.repositories.message.chat_id == chat_id)
        )

        if cursor:
            try:
                created, message_id = decode_message_cursor(cursor)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid cursor") from exc

            if direction == "before":
                query = query.where(
                    or_(
                        self.container.repositories.message.created < created,
                        and_(
                            self.container.repositories.message.created == created,
                            self.container.repositories.message.id < message_id,
                        ),
                    )
                )
            else:
                query = query.where(
                    or_(
                        self.container.repositories.message.created > created,
                        and_(
                            self.container.repositories.message.created == created,
                            self.container.repositories.message.id > message_id,
                        ),
                    )
                )

        order = (
            [desc(self.container.repositories.message.created), desc(self.container.repositories.message.id)]
            if direction == "before"
            else [self.container.repositories.message.created, self.container.repositories.message.id]
        )
        rows = await session.execute(query.order_by(*order).limit(limit + 1))
        messages = list(rows.scalars())
        has_more = len(messages) > limit
        messages = messages[:limit]

        if direction == "before":
            messages.reverse()

        prev_cursor = encode_message_cursor(messages[0].created, messages[0].id) if messages else None
        next_cursor = encode_message_cursor(messages[-1].created, messages[-1].id) if messages else None

        return {
            "items": messages,
            "has_more": has_more,
            "prev_cursor": prev_cursor,
            "next_cursor": next_cursor,
        }
