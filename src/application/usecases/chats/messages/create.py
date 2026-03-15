import typing
import uuid

from fastapi import HTTPException

from src.application.usecases.chats.collections import ChatMemberRequired
from src.application.utils.chats.message import compute_shard_key
from src.common.formats.utils import date
from src.infrastructure.databases.orm.sqlalchemy import queries
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres.crud import Chat
from src.infrastructure.databases.postgres.crud import File
from src.infrastructure.databases.postgres.crud import Member
from src.infrastructure.databases.postgres.crud import Message
from src.infrastructure.databases.postgres.crud import MessageFile


class Repositories:
    def __init__(self, session: Session) -> None:
        self.chat = Chat
        self.file = File
        self.member = Member
        self.message = Message
        self.message_file = MessageFile
        self.session = session


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repositories: Repositories, security: Security) -> None:
        self.repositories = repositories
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(self, *, chat_id: uuid.UUID, user_id: str) -> typing.Any:
        session = self.container.repositories.session
        chat = await session.get(self.container.repositories.chat.table, chat_id)
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")

        member = await self.container.repositories.member.user(
            session,
            queries.Filter.eq(key="chat_id", value=chat.id),
            queries.Filter.eq(key="shard_id", value=chat.shard_id),
            queries.Filter.eq(key="user_id", value=user_id),
        )
        if member is None:
            raise ChatMemberRequired
        return chat, member

    async def ensure_direct_chat(
        self,
        user_a: str,
        user_b: str,
    ) -> tuple[typing.Any, list[str]]:
        session = self.container.repositories.session
        if chat := await self.container.repositories.chat.direct(session, user_a, user_b):
            return chat, await self.container.repositories.member.ids(
                session,
                queries.Filter.eq(key="chat_id", value=chat.id),
            )

        members = sorted([user_a, user_b])
        chat = await self.container.repositories.chat.create(
            session,
            {
                "id": uuid.uuid4(),
                "kind": "direct",
                "shard_id": compute_shard_key(":".join(members)),
                "created": date.now(),
            },
        )
        await self.container.repositories.member.create(
            session,
            {
                "id": uuid.uuid4(),
                "shard_id": chat.shard_id,
                "chat_id": chat.id,
                "user_id": user_a,
                "created": date.now(),
            },
        )
        await self.container.repositories.member.create(
            session,
            {
                "id": uuid.uuid4(),
                "shard_id": chat.shard_id,
                "chat_id": chat.id,
                "user_id": user_b,
                "created": date.now(),
            },
        )
        return chat, members

    async def attach_files(
        self,
        message_id: uuid.UUID,
        chat_id: uuid.UUID,
        shard_id: int,
        attachments: list[dict[str, object]],
    ) -> None:
        session = self.container.repositories.session
        for position, attachment in enumerate(attachments):
            file = None
            raw_id = attachment.get("id")
            if isinstance(raw_id, str):
                try:
                    file = await session.get(self.container.repositories.file.table, uuid.UUID(raw_id))
                except ValueError:
                    raise HTTPException(status_code=400, detail="Attachment id is invalid")

            bucket = attachment.get("bucket")
            key = attachment.get("key") or attachment.get("path")
            if file is None and (not isinstance(bucket, str) or not isinstance(key, str)):
                raise HTTPException(status_code=400, detail="Attachment id or bucket/key are required")

            if file is None:
                file = await self.container.repositories.file.by_storage_key(session, bucket, key)
            if file is None:
                file = await self.container.repositories.file.create(
                    session,
                    {
                        "id": uuid.uuid4(),
                        "storage": attachment.get("storage", "s3"),
                        "bucket": bucket,
                        "key": key,
                        "filename": attachment.get("filename") or attachment.get("name"),
                        "content_type": attachment.get("content_type"),
                        "size_bytes": attachment.get("size_bytes") or attachment.get("size"),
                        "created": date.now(),
                    },
                )

            await self.container.repositories.message_file.create(
                session,
                {
                    "id": uuid.uuid4(),
                    "shard_id": shard_id,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "file_id": file.id,
                    "position": position,
                    "created": date.now(),
                },
            )

    async def __call__(
        self,
        *,
        sender_id: str,
        body: str,
        attachments: list[dict[str, object]],
        chat_id: uuid.UUID | None = None,
        peer_user_id: str | None = None,
    ) -> dict[str, typing.Any]:
        session = self.container.repositories.session

        if not body and not attachments:
            raise HTTPException(status_code=400, detail="Message body or attachments required")
        if not chat_id and not peer_user_id:
            raise HTTPException(status_code=400, detail="chat_id or peer_user_id is required")

        if chat_id:
            chat, sender = await self.validate(chat_id=chat_id, user_id=sender_id)
            member_ids = await self.container.repositories.member.ids(
                session,
                queries.Filter.eq(key="chat_id", value=chat.id),
                queries.Filter.eq(key="shard_id", value=chat.shard_id),
            )
        else:
            chat, member_ids = await self.ensure_direct_chat(sender_id, peer_user_id)
            sender = await self.container.repositories.member.user(
                session,
                queries.Filter.eq(key="chat_id", value=chat.id),
                queries.Filter.eq(key="shard_id", value=chat.shard_id),
                queries.Filter.eq(key="user_id", value=sender_id),
            )
            if sender is None:
                raise HTTPException(status_code=500, detail="Sender member was not created")

        message = await self.container.repositories.message.create(
            session,
            {
                "id": uuid.uuid4(),
                "shard_id": chat.shard_id,
                "chat_id": chat.id,
                "member_id": sender.id,
                "body": body,
                "created": date.now(),
            },
        )
        await self.attach_files(message.id, chat.id, chat.shard_id, attachments)
        message = await self.container.repositories.message.relations(
            session,
            queries.Filter.eq(key="id", value=message.id),
        )
        return {
            "event": "message.created",
            "chat": chat,
            "message": message,
            "recipients": member_ids,
        }
