import typing
import uuid

from pydantic import Field

from src.entrypoints.http.common.schemas import Command
from src.entrypoints.http.common.schemas import Paginated
from src.entrypoints.http.common.schemas import Pagination
from src.entrypoints.http.common.schemas import Query
from src.entrypoints.http.common.schemas import Request
from src.entrypoints.http.common.schemas import Response
from src.infrastructure.databases.orm.sqlalchemy.collections import Direction
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


class ReorderChats(Public, Request, Command):
    chats: list[uuid.UUID] = Field(default_factory=list)


class ReadMessages(Public, Request, Command):
    message_id: uuid.UUID = Field(alias="message")


class SearchChats(Public, Request, Query):
    class SearchChatsFilters(Public, Request, Query):
        text: str | None = None

    class SearchChatsSorting(Public, Request, Query):
        field: typing.Literal["activity_at"] = "activity_at"
        direction: Direction = Direction.desc

    class SearchChatsPagination(Public, Request, Query, Pagination): ...

    filters: SearchChatsFilters = Field(default_factory=SearchChatsFilters)
    sorting: SearchChatsSorting = Field(default_factory=SearchChatsSorting)
    pagination: SearchChatsPagination

    def deserialize(self) -> dict[str, typing.Any]:
        return self.model_dump()


class SearchMessages(Public, Request, Query):
    class SearchMessagesFilters(Public, Request, Query):
        text: str | None = None

    class SearchMessagesSorting(Public, Request, Query):
        field: typing.Literal["created"] = "created"
        direction: Direction = Direction.desc

    class SearchMessagesPagination(Public, Request, Query, Pagination): ...

    filters: SearchMessagesFilters = Field(default_factory=SearchMessagesFilters)
    sorting: SearchMessagesSorting = Field(default_factory=SearchMessagesSorting)
    pagination: SearchMessagesPagination

    def deserialize(self) -> dict[str, typing.Any]:
        return self.model_dump()


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
    is_read: bool
    pinned_at: str | None
    created: str

    @classmethod
    def serialize(cls, row: typing.Any) -> typing.Self:
        message = row["message"] if isinstance(row, dict) else row
        is_read = bool(row.get("is_read")) if isinstance(row, dict) else False
        return cls(
            id=str(message.id),
            chat_id=str(message.chat_id),
            sender_id=message.member.user_id,
            member_id=str(message.member_id),
            body=message.body,
            attachments=[Attachment.serialize(attachment) for attachment in message.attachments],
            is_read=is_read,
            pinned_at=message.pinned_at.isoformat() if message.pinned_at else None,
            created=message.created.isoformat(),
        )


class Messages(Public, Response, Paginated):
    items: list[Message]

    @classmethod
    def serialize(
        cls,
        *,
        items: list[typing.Any],
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
        message: typing.Any,
        recipients: list[str],
    ) -> dict[str, typing.Any]:
        return cls(
            event="message.created",
            chat_id=chat_id,
            message=Message.serialize(message),
            recipients=recipients,
        ).model_dump()


class Chat(Public, Response):
    class Member(Public, Response):
        user_id: str
        online: bool
        last_seen_at: str | None

        @classmethod
        def serialize(cls, row: typing.Any) -> typing.Self:
            if isinstance(row, str):
                return cls(user_id=row, online=False, last_seen_at=None)
            return cls(
                user_id=row["user_id"],
                online=bool(row["online"]),
                last_seen_at=row["last_seen_at"].isoformat() if row["last_seen_at"] is not None else None,
            )

    chat_id: str
    kind: str
    title: str | None
    members: list[Member]
    pin_position: int | None
    unread_count: int
    last_message_preview: str | None
    last_message_at: str | None

    @classmethod
    def serialize(
        cls,
        *,
        chat: _Chat,
        members: list[typing.Any],
        pin_position: int | None,
        unread_count: int,
        last_message: _Message | None,
    ) -> typing.Self:
        return cls(
            chat_id=str(chat.id),
            kind=chat.kind,
            title=chat.title,
            members=[cls.Member.serialize(member) for member in members],
            pin_position=pin_position,
            unread_count=unread_count,
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
                    pin_position=item["pin_position"],
                    unread_count=item["unread_count"],
                    last_message=item["last_message"],
                )
                for item in items
            ],
        )
