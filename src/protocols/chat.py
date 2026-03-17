import datetime
import typing

from pydantic import BaseModel
from pydantic import Field

from src.common.formats.utils import field
from src.infrastructure.databases.postgres.tables import Chat as _Chat
from src.infrastructure.databases.postgres.tables import File as _File
from src.infrastructure.databases.postgres.tables import Member as _Member
from src.infrastructure.databases.postgres.tables import Message as _Message
from src.infrastructure.databases.postgres.tables import User as _User


class File(BaseModel):
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


class Member(BaseModel):
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


class BaseMessage(BaseModel):
    id: str
    kind: str
    text: str | None
    attachments: list[File]
    pinned: datetime.datetime | None
    edited: datetime.datetime | None
    created: datetime.datetime
    member: Member | None

    @classmethod
    def serialize(cls, message: _Message) -> typing.Self:
        attachments = getattr(message, "attachments", [])
        member = getattr(message, "member", None)

        return cls(
            id=message.id,
            kind=message.kind,
            text=message.text,
            attachments=[File.serialize(file) for file in attachments],
            pinned=message.pinned,
            edited=message.edited,
            created=message.created,
            member=Member.serialize(member) if member else None,
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


class Chat(BaseModel):
    id: str
    title: str
    members: list[Member] = Field(default_factory=list)

    @classmethod
    def serialize(cls, user: _User, chat: _Chat) -> typing.Self:
        members = getattr(chat, "members", [])
        return cls(
            id=chat.id,
            title=chat.title,
            members=[Member.serialize(member=member, current=member.user_id == user.id) for member in members],
        )
