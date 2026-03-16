import typing
import uuid

from fastapi import HTTPException

from src.application.collections import ChatMemberRequired
from src.application.utils.chats.message import compute_shard_key
from src.common.formats.utils import date
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat = adapters.repositories.Chat(session)
        self.chat_member = adapters.repositories.ChatMember(session)
        self.file = adapters.repositories.File(session)
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)
        self.message_file = adapters.repositories.MessageFile(session)
        self.message_read = adapters.repositories.MessageRead(session)


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repository: Repository, security: Security) -> None:
        self.repository = repository
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(self, chat_id: uuid.UUID, user_id: str) -> typing.Any:
        chat = await self.container.repository.chat.one(Filter.eq("id", chat_id))
        chat_member = await self.container.repository.chat_member.user(chat_id=chat.id, user_id=user_id)
        if chat_member is None:
            raise ChatMemberRequired
        return chat, chat_member

    async def ensure_direct_chat(
        self,
        user_a: str,
        user_b: str,
    ) -> tuple[typing.Any, list[str]]:
        if chat := await self.container.repository.chat.direct(user_a, user_b):
            return chat, await self.container.repository.chat_member.user_ids(chat.id, chat.shard_id)

        members = sorted([user_a, user_b])
        created = date.now()
        chat = await self.container.repository.chat.create(
            {
                "id": uuid.uuid4(),
                "kind": "direct",
                "options": {},
                "shard_id": compute_shard_key(":".join(members)),
                "created": created,
            },
        )
        member_a = await self.container.repository.member.ensure(user_id=user_a, created=created)
        member_b = await self.container.repository.member.ensure(user_id=user_b, created=created)
        await self.container.repository.chat_member.create(
            {
                "id": uuid.uuid4(),
                "shard_id": chat.shard_id,
                "chat_id": chat.id,
                "member_id": member_a.id,
                "created": created,
            },
        )
        await self.container.repository.chat_member.create(
            {
                "id": uuid.uuid4(),
                "shard_id": chat.shard_id,
                "chat_id": chat.id,
                "member_id": member_b.id,
                "created": created,
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
        for position, attachment in enumerate(attachments):
            file = None
            raw_id = attachment.get("id")
            if isinstance(raw_id, str):
                try:
                    file_id = uuid.UUID(raw_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Attachment id is invalid")
                if await self.container.repository.file.exists(Filter.eq("id", file_id)):
                    file = await self.container.repository.file.one(Filter.eq("id", file_id))

            bucket = attachment.get("bucket")
            key = attachment.get("key") or attachment.get("path")
            if file is None and (not isinstance(bucket, str) or not isinstance(key, str)):
                raise HTTPException(status_code=400, detail="Attachment id or bucket/key are required")

            if file is None:
                file = await self.container.repository.file.by_storage_key(bucket, key)
            if file is None:
                file = await self.container.repository.file.create(
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

            await self.container.repository.message_file.create(
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
        sender_id: str,
        body: str,
        attachments: list[dict[str, object]],
        chat_id: uuid.UUID | None = None,
        peer_user_id: str | None = None,
    ) -> dict[str, typing.Any]:
        if not body and not attachments:
            raise HTTPException(status_code=400, detail="Message body or attachments required")
        if not chat_id and not peer_user_id:
            raise HTTPException(status_code=400, detail="chat_id or peer_user_id is required")

        if chat_id:
            chat, sender = await self.validate(chat_id=chat_id, user_id=sender_id)
            member_ids = await self.container.repository.chat_member.user_ids(chat.id, chat.shard_id)
        else:
            chat, member_ids = await self.ensure_direct_chat(sender_id, peer_user_id)
            sender = await self.container.repository.chat_member.user(chat_id=chat.id, user_id=sender_id)
            if sender is None:
                raise ChatMemberRequired

        created = date.now()
        message = await self.container.repository.message.create(
            {
                "id": uuid.uuid4(),
                "shard_id": chat.shard_id,
                "chat_id": chat.id,
                "member_id": sender.member_id,
                "body": body,
                "created": created,
            },
        )
        await self.attach_files(message.id, chat.id, chat.shard_id, attachments)
        await self.container.repository.chat_member.mark_read(chat_member_id=sender.id, read_at=created)
        message = await self.container.repository.message.relations(
            Filter.eq("id", message.id),
        )
        return {
            "event": "message.created",
            "chat": chat,
            "message": {"message": message, "is_read": False},
            "recipients": member_ids,
        }
