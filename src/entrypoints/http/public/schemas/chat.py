import typing

from pydantic import Field

from src.entrypoints.http.common.schemas import Command
from src.entrypoints.http.common.schemas import Paginated
from src.entrypoints.http.common.schemas import Pagination
from src.entrypoints.http.common.schemas import Query
from src.entrypoints.http.common.schemas import Request
from src.entrypoints.http.common.schemas import Response
from src.infrastructure.databases.postgres.tables import Chat as _Chat
from src.infrastructure.databases.postgres.tables import File as _File
from src.infrastructure.databases.postgres.tables import Message as _Message
from src.infrastructure.databases.postgres.tables import MessageFile as _MessageFile

from .base import Public


class CreateMessage(Public, Request, Command):
    body: str = ""
    attachments: list[dict[str, typing.Any]] = Field(default_factory=list)


class CreateChat(Public, Request, Command):
    members: list[str] = Field(default_factory=list)


class SearchChats(Public, Request, Query, Pagination):
    text: str | None = None


class SearchMessages(Public, Request, Query, Pagination):
    direction: str = "before"
    text: str | None = None


class Attachment(Public, Response):
    id: str
    storage: str
    bucket: str
    key: str
    filename: str | None
    content_type: str | None
    size_bytes: int | None
    position: int

    @classmethod
    def serialize(cls, row: _MessageFile) -> typing.Self:
        return cls(
            id=str(row.file.id),
            storage=row.file.storage,
            bucket=row.file.bucket,
            key=row.file.key,
            filename=row.file.filename,
            content_type=row.file.content_type,
            size_bytes=row.file.size_bytes,
            position=row.position,
        )


class UploadedFile(Public, Response):
    id: str
    storage: str
    bucket: str
    key: str
    filename: str | None
    content_type: str | None
    size_bytes: int | None

    @classmethod
    def serialize(cls, row: _File) -> typing.Self:
        return cls(
            id=str(row.id),
            storage=row.storage,
            bucket=row.bucket,
            key=row.key,
            filename=row.filename,
            content_type=row.content_type,
            size_bytes=row.size_bytes,
        )


class Message(Public, Response):
    id: str
    chat_id: str
    sender_id: str
    member_id: str
    body: str | None
    attachments: list[Attachment]
    created: str

    @classmethod
    def serialize(cls, row: _Message) -> typing.Self:
        return cls(
            id=str(row.id),
            chat_id=str(row.chat_id),
            sender_id=row.member.user_id,
            member_id=str(row.member_id),
            body=row.body,
            attachments=[Attachment.serialize(attachment) for attachment in row.attachments],
            created=row.created.isoformat(),
        )


class Messages(Public, Response, Paginated):
    items: list[Message]

    @classmethod
    def serialize(
        cls,
        *,
        items: list[_Message],
        has_more: bool,
        prev_cursor: str | None,
        next_cursor: str | None,
    ) -> typing.Self:
        return cls(
            items=[Message.serialize(item) for item in items],
            has_more=has_more,
            prev_cursor=prev_cursor,
            next_cursor=next_cursor,
        )


class MessageCreated(Public, Response):
    event: str
    chat_id: str
    message: Message
    recipients: list[str]

    @classmethod
    def serialize(
        cls,
        *,
        chat_id: str,
        message: _Message,
        recipients: list[str],
    ) -> dict[str, typing.Any]:
        return cls(
            event="message.created",
            chat_id=chat_id,
            message=Message.serialize(message),
            recipients=recipients,
        ).model_dump()


class Chat(Public, Response):
    chat_id: str
    kind: str
    title: str | None
    members: list[str]
    last_message_preview: str | None
    last_message_at: str | None

    @classmethod
    def serialize(
        cls,
        *,
        chat: _Chat,
        members: list[str],
        last_message: _Message | None,
    ) -> typing.Self:
        return cls(
            chat_id=str(chat.id),
            kind=chat.kind,
            title=chat.title,
            members=members,
            last_message_preview=last_message.body if last_message else None,
            last_message_at=last_message.created.isoformat() if last_message and last_message.created else None,
        )


class Chats(Public, Response, Paginated):
    items: list[Chat]

    @classmethod
    def serialize(
        cls,
        *,
        items: list[dict[str, typing.Any]],
        has_more: bool,
        prev_cursor: str | None,
        next_cursor: str | None,
    ) -> typing.Self:
        return cls(
            has_more=has_more,
            prev_cursor=prev_cursor,
            next_cursor=next_cursor,
            items=[
                Chat.serialize(
                    chat=item["chat"],
                    members=item["members"],
                    last_message=item["last_message"],
                )
                for item in items
            ],
        )
