import datetime
import typing

from pydantic import BaseModel
from pydantic import Field

from src.common.formats.utils import field
from src.configuration import settings
from src.infrastructure.databases.postgres.tables import Chat as _Chat
from src.infrastructure.databases.postgres.tables import File as _File
from src.infrastructure.databases.postgres.tables import Member as _Member
from src.infrastructure.databases.postgres.tables import Message as _Message


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
            url=f"{settings.MINIO_HOST.rstrip('/')}/{settings.MINIO_BUCKET}{file.path}",
        )


class Member(BaseModel):
    id: str
    user_id: str
    role: str
    position: int | None = None
    notifications: int | None = None

    @classmethod
    def serialize(cls, member: _Member) -> typing.Self:
        role = field.required(getattr(member, "role"))
        return cls(
            id=member.id,
            user_id=member.user_id,
            role=role.id,
            position=member.position,
            notifications=member.notifications,
        )


class BaseMessage(BaseModel):
    id: str
    kind: str
    text: str | None
    pinned: datetime.datetime | None
    edited: datetime.datetime | None
    created: datetime.datetime
    member: Member | None

    @classmethod
    def serialize(cls, message: _Message) -> typing.Self:
        member = getattr(message, "member", None)

        return cls(
            id=message.id,
            kind=message.kind,
            text=message.text,
            pinned=message.pinned,
            edited=message.edited,
            created=message.created,
            member=Member.serialize(member) if member else None,
        )


class Message(BaseMessage):
    class Reply(BaseMessage): ...

    class Forward(BaseMessage): ...

    chat: "Chat | None"
    attachments: list[File]
    reply: Reply | None
    forward: Forward | None

    @classmethod
    def serialize(cls, message: _Message) -> typing.Self:
        attachments = getattr(message, "attachments", [])
        chat = getattr(message, "chat")
        reply = getattr(message, "reply")
        forward = getattr(message, "forward")

        return cls(
            **BaseMessage.serialize(message).model_dump(),
            chat=Chat.serialize(chat=chat) if chat else None,
            attachments=[File.serialize(file) for file in attachments],
            reply=cls.Reply.serialize(reply) if reply else None,
            forward=cls.Forward.serialize(forward) if forward else None,
        )


class Chat(BaseModel):
    id: str
    title: str
    members: list[Member] = Field(default_factory=list)

    @classmethod
    def serialize(cls, chat: _Chat) -> typing.Self:
        members = getattr(chat, "members", [])

        return cls(
            id=chat.id,
            title=chat.title,
            members=[Member.serialize(member=member) for member in members],
        )
