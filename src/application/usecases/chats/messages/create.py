import typing
import uuid

from fastapi import HTTPException

from src.application.collections import MemberRequired
from src.common.formats.utils import date
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat = adapters.repositories.Chat(session)
        self.file = adapters.repositories.File(session)
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)
        self.attachment = adapters.repositories.Attachment(session)
        self.read = adapters.repositories.Read(session)
        self.forward = adapters.repositories.Forward(session)
        self.reply = adapters.repositories.Reply(session)
        self.role = adapters.repositories.Role(session)
        self.user = adapters.repositories.User(session)


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
        member = await self.container.repository.member.user(chat_id=chat.id, user_id=user_id)
        if member is None:
            raise MemberRequired
        return chat, member

    async def ensure_direct_chat(
        self,
        user_a: str,
        user_b: str,
    ) -> tuple[typing.Any, list[str]]:
        if chat := await self.container.repository.chat.direct(user_a, user_b):
            return chat, await self.container.repository.member.user_ids(chat.id)

        members = sorted([user_a, user_b])
        created = date.now()
        user_role = await self.container.repository.role.ensure(name="user")
        chat = await self.container.repository.chat.create(
            {
                "id": str(uuid.uuid4()),
                "title": None,
                "options": {},
                "created": created,
            },
        )
        user_a_row = await self.container.repository.user.ensure(external_id=user_a)
        user_b_row = await self.container.repository.user.ensure(external_id=user_b)
        await self.container.repository.member.create(
            {
                "id": str(uuid.uuid4()),
                "chat_id": chat.id,
                "user_id": user_a_row.id,
                "role_id": user_role.id,
                "position": None,
                "notifications": 0,
            },
        )
        await self.container.repository.member.create(
            {
                "id": str(uuid.uuid4()),
                "chat_id": chat.id,
                "user_id": user_b_row.id,
                "role_id": user_role.id,
                "position": None,
                "notifications": 0,
            },
        )
        return chat, members

    async def attach_files(
        self,
        message_id: uuid.UUID,
        attachments: list[dict[str, object]],
    ) -> None:
        for attachment in attachments:
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
                        "id": str(uuid.uuid4()),
                        "storage": attachment.get("storage", "s3"),
                        "bucket": bucket,
                        "key": key,
                        "filename": attachment.get("filename") or attachment.get("name"),
                        "content_type": attachment.get("content_type"),
                        "size_bytes": attachment.get("size_bytes") or attachment.get("size"),
                        "created": date.now(),
                    },
                )

            await self.container.repository.attachment.create(
                {
                    "id": str(uuid.uuid4()),
                    "message_id": message_id,
                    "file_id": file.id,
                },
            )

    async def attach_reply(
        self,
        message_id: uuid.UUID,
        chat_id: uuid.UUID,
        reply_message_id: uuid.UUID | None,
    ) -> None:
        if reply_message_id is None:
            return

        await self.container.repository.message.one(
            Filter.eq("id", reply_message_id),
            Filter.eq("chat_id", chat_id),
        )
        await self.container.repository.reply.create(
            {
                "id": str(uuid.uuid4()),
                "message_id": message_id,
                "source_message_id": reply_message_id,
                "created": date.now(),
            },
        )

    async def attach_forward(
        self,
        message_id: uuid.UUID,
        chat_id: uuid.UUID,
        sender_id: str,
        forward: dict[str, uuid.UUID] | None,
    ) -> None:
        if forward is None:
            return

        source_member = await self.container.repository.member.user(
            chat_id=forward["chat_id"],
            user_id=sender_id,
        )
        if source_member is None:
            raise MemberRequired

        source_message = await self.container.repository.message.one(
            Filter.eq("id", forward["message_id"]),
            Filter.eq("chat_id", forward["chat_id"]),
        )
        await self.container.repository.forward.create(
            {
                "id": str(uuid.uuid4()),
                "message_id": message_id,
                "source_message_id": source_message.id,
                "created": date.now(),
            },
        )

    async def __call__(
        self,
        sender_id: str,
        body: str,
        reply_message_id: uuid.UUID | None,
        forward: dict[str, uuid.UUID] | None,
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
            member_ids = await self.container.repository.member.user_ids(chat.id)
        else:
            chat, member_ids = await self.ensure_direct_chat(sender_id, peer_user_id)
            sender = await self.container.repository.member.user(chat_id=chat.id, user_id=sender_id)
            if sender is None:
                raise MemberRequired

        created = date.now()
        sender_user = await self.container.repository.user.ensure(external_id=sender_id)
        message = await self.container.repository.message.create(
            {
                "id": str(uuid.uuid4()),
                "chat_id": chat.id,
                "user_id": sender_user.id,
                "member_id": sender.id,
                "kind": "message",
                "text": body,
                "pinned": None,
                "edited": None,
                "created": created,
            },
        )
        await self.attach_files(message.id, attachments)
        await self.attach_reply(message.id, chat.id, reply_message_id)
        await self.attach_forward(message.id, chat.id, sender_id, forward)
        await self.container.repository.member.mark_read(
            chat_member_id=sender.id,
            message_id=message.id,
            read=created,
            unread_count=0,
        )
        await self.container.repository.member.increment_unread(
            chat_id=chat.id,
            shard_id=None,
            excluded_chat_member_id=sender.id,
        )
        message = await self.container.repository.message.relations(
            Filter.eq("id", message.id),
        )
        return {
            "event": "message.created",
            "chat": chat,
            "message": {"message": message, "is_read": False},
            "recipients": member_ids,
        }
