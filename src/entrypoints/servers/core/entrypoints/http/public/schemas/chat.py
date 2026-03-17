import typing

from pydantic import Field

from src.common.formats.utils import field
from src.common.typings.validators import Search
from src.entrypoints.http.common.schemas import Paginated
from src.entrypoints.http.common.schemas import Pagination
from src.entrypoints.http.common.schemas import Query
from src.entrypoints.http.common.schemas import Request
from src.entrypoints.http.common.schemas import Response
from src.infrastructure.databases.postgres.tables import Chat as _Chat
from src.infrastructure.databases.postgres.tables import File as _File
from src.infrastructure.databases.postgres.tables import Member as _Member
from src.infrastructure.databases.postgres.tables import Message as _Message
from src.infrastructure.databases.postgres.tables import User as _User

from .base import Public


class SearchChats(Public, Request, Query):
    class Filters(Public, Request, Query):
        text: Search | None = None

    class CursorPagination(Public, Request, Query, Pagination): ...

    filters: Filters = Field(default_factory=Filters)
    pagination: CursorPagination = Field(default_factory=CursorPagination)


class SearchMessages(Public, Request, Query):
    class Filters(Public, Request, Query):
        text: Search | None = None

    class CursorPagination(Public, Request, Query, Pagination): ...

    filters: Filters = Field(default_factory=Filters)
    pagination: CursorPagination = Field(default_factory=CursorPagination)


class File(Public, Response):
    id: str
    filename: str | None
    content_type: str | None
    path: str
    url: str

    @classmethod
    def serialize(cls, file: _File) -> typing.Self:
        return cls(
            id=file.id,
            filename=file.filename,
            content_type=file.content_type,
            path=file.path,
            url=file.path,
        )


class Member(Public, Response):
    id: str
    user_id: str
    role: str
    position: int | None = None
    notifications: int | None = None

    @classmethod
    def serialize(cls, member: _Member, current: bool = False) -> typing.Self:
        role = field.required(getattr(member, "role"))
        return cls(
            id=member.id,
            user_id=member.user_id,
            role=role.id,
            position=member.position if current else None,
            notifications=member.notifications if current else None,
        )


class BaseMessage(Public, Response):
    class Read(Public, Response):
        id: str
        created: str

        @classmethod
        def serialize(cls, read: typing.Any) -> typing.Self:
            return cls(id=read.id, created=read.created.isoformat())

    id: str
    kind: str
    text: str | None
    attachments: list[File]
    pinned: str | None
    edited: str | None
    created: str
    member: Member | None
    read: Read | None

    @classmethod
    def serialize(cls, message: _Message) -> typing.Self:
        attachments = getattr(message, "attachments", [])
        member = getattr(message, "member", None)
        reads = getattr(message, "reads", [])
        read = reads[0] if reads else None

        return cls(
            id=message.id,
            kind=message.kind,
            text=message.text,
            attachments=[File.serialize(file) for file in attachments],
            pinned=message.pinned.isoformat() if message.pinned else None,
            edited=message.edited.isoformat() if message.edited else None,
            created=message.created.isoformat(),
            member=Member.serialize(member) if member else None,
            read=cls.Read.serialize(read) if read else None,
        )


class Message(BaseMessage):
    class Reply(BaseMessage): ...

    class Forward(BaseMessage): ...

    reply: Reply | None
    forward: Forward | None

    @classmethod
    def serialize(cls, message: _Message) -> typing.Self:
        reply = getattr(message, "reply", None)
        forward = getattr(message, "forward", None)

        return cls(
            **BaseMessage.serialize(message).model_dump(),
            reply=cls.Reply.serialize(reply) if reply else None,
            forward=cls.Forward.serialize(forward) if forward else None,
        )


class Messages(Public, Response, Paginated):
    items: list[Message]

    @classmethod
    def serialize(
        cls,
        messages: list[_Message],
        more: bool,
        prev: str | None,
        next: str | None,
    ) -> typing.Self:
        return cls(
            items=[Message.serialize(message) for message in messages],
            more=more,
            prev=prev,
            next=next,
        )


class Chat(Public, Response):
    id: str
    title: str | None
    members: list[Member] = Field(default_factory=list)

    @classmethod
    def serialize(cls, user: _User, chat: _Chat) -> typing.Self:
        members = getattr(chat, "members", [])
        return cls(
            id=chat.id,
            title=chat.title,
            members=[Member.serialize(member=member, current=member.user_id == user.id) for member in members],
        )


class Chats(Public, Response, Paginated):
    items: list[Chat]

    @classmethod
    def serialize(
        cls,
        user: _User,
        chats: list[_Chat],
        more: bool,
        prev: str | None,
        next: str | None,
    ) -> typing.Self:
        return cls(
            items=[Chat.serialize(user=user, chat=chat) for chat in chats],
            more=more,
            prev=prev,
            next=next,
        )
