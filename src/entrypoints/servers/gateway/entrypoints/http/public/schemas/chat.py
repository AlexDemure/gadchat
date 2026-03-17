import typing

from typing import Literal

from pydantic import Field

from src.common.formats.utils import date
from src.entrypoints.http.common.schemas import Command
from src.entrypoints.http.common.schemas import Request
from src.entrypoints.http.common.schemas import Response

from .base import Public


class Event(Public, Response):
    id: str
    topic: str
    priority: int
    payload: dict[str, typing.Any] = Field(default_factory=dict)
    created: str
    dispatched: str | None = None
    completed: str | None = None
    failed: str | None = None
    error: str | None = None

    @classmethod
    def mock(cls, topic: str) -> typing.Self:
        return cls(
            id="pending",
            topic=topic,
            priority=100,
            payload={},
            created=date.now().isoformat(),
            dispatched=None,
            completed=None,
            failed=None,
            error=None,
        )


class ChatMember(Public):
    id: str | None = None
    user_id: str
    role: str | None = None
    position: int | None = None
    notifications: int | None = None


class Chat(Public):
    id: str
    title: str | None = None
    members: list[ChatMember] = Field(default_factory=list)


class MessageAttachment(Public):
    id: str | None = None
    filename: str | None = None
    content_type: str | None = None
    path: str | None = None
    url: str | None = None
    content: str | None = Field(default=None, description="Base64 encoded content when sent over websocket")


class Message(Public):
    chat_id: str
    text: str | None = None
    file_ids: list[str] = Field(default_factory=list, alias="files")


class CreateMessageReply(Message):
    message_id: str = Field(alias="message")
    chat_id: str | None = None


class CreateMessageForward(Message):
    message_id: str = Field(alias="message")
    chat_id: str | None = Field(default=None, alias="chat")


class ChatMessageRead(Public):
    id: str
    created: str


class ChatMessage(Message):
    id: str | None = None
    kind: str | None = None
    attachments: list[MessageAttachment] = Field(default_factory=list)
    pinned: str | None = None
    edited: str | None = None
    created: str | None = None
    member: ChatMember | None = None
    read: ChatMessageRead | None = None
    reply: CreateMessageReply | None = None
    forward: CreateMessageForward | None = None


class Chats(Response, Public):
    event: Literal["chats.found"] = "chats.found"
    request_id: str | None = None
    items: list[Chat] = Field(default_factory=list)
    more: bool = False
    prev: str | None = None
    next: str | None = None


class Messages(Response, Public):
    event: Literal["messages.found"] = "messages.found"
    request_id: str | None = None
    items: list[ChatMessage] = Field(default_factory=list)
    more: bool = False
    prev: str | None = None
    next: str | None = None


class ChatAccepted(Response, Public):
    event: Literal["chat.create.accepted"] = "chat.create.accepted"
    request_id: str | None = None
    task: Event


class ChatEvent(Response, Public):
    event: Literal["chat.created"] = "chat.created"
    request_id: str | None = None
    chat: Chat


class MessageEvent(Response, Public):
    event: Literal["message.created"] = "message.created"
    request_id: str | None = None
    message: ChatMessage


class MessageReadEvent(Response, Public):
    event: Literal["message.read"] = "message.read"
    request_id: str | None = None
    chat_id: str
    message_id: str
    member_id: str | None = None
    created: str | None = None


class MessagePinnedEvent(Response, Public):
    event: Literal["message.pinned"] = "message.pinned"
    request_id: str | None = None
    chat_id: str
    message_id: str
    pinned: str | None = None


class MessageUnpinnedEvent(Response, Public):
    event: Literal["message.unpinned"] = "message.unpinned"
    request_id: str | None = None
    chat_id: str
    message_id: str


class PositionChatEvent(Response, Public):
    event: Literal["chat.position.updated"] = "chat.position.updated"
    request_id: str | None = None
    chat_id: str
    position: int | None = None


class CreateChat(Public, Request, Command):
    class Payload(Public):
        title: str | None = None
        user_ids: list[str] = Field(default_factory=list, alias="users")

    id: str | None = Field(default=None, description="Client correlation id")
    type: Literal["chat.create.command"] = "chat.create.command"
    payload: Payload


class PositionChat(Public, Request, Command):
    class Payload(Public):
        chat_id: str
        position: int | None = None

    id: str | None = Field(default=None, description="Client correlation id")
    type: Literal["chat.position.command"] = "chat.position.command"
    payload: Payload


class CreateMessage(Public, Request, Command):
    class Payload(Message):
        reply: CreateMessageReply | None = None
        forward: CreateMessageForward | None = None

    id: str | None = Field(default=None, description="Client correlation id")
    type: Literal["message.create.command"] = "message.create.command"
    payload: Payload


class PinnedMessage(Public, Request, Command):
    class Payload(Public):
        chat_id: str
        message_id: str

    id: str | None = Field(default=None, description="Client correlation id")
    type: Literal["message.pinned.command"] = "message.pinned.command"
    payload: Payload


class UnpinnedMessage(Public, Request, Command):
    class Payload(Public):
        chat_id: str
        message_id: str

    id: str | None = Field(default=None, description="Client correlation id")
    type: Literal["message.unpinned.command"] = "message.unpinned.command"
    payload: Payload


class ReadMessage(Public, Request, Command):
    class Payload(Public):
        chat_id: str
        message_id: str

    id: str | None = Field(default=None, description="Client correlation id")
    type: Literal["message.read.command"] = "message.read.command"
    payload: Payload
