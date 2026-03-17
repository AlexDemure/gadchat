import datetime

from typing import Literal

from src.protocols.chat import Chat
from src.protocols.chat import Message

from .base import Event


class CreateChat(Event):
    event: Literal["chat.create.event"]
    chat: Chat


class CreateMessage(Event):
    event: Literal["message.create.event"]
    message: Message


class ReadMessage(Event):
    event: Literal["message.read.event"]
    chat_id: str
    message_id: str
    member_id: str
    created: datetime.datetime


class PinMessage(Event):
    event: Literal["message.pin.event"]
    chat_id: str
    message_id: str
    pinned: datetime.datetime


class UnpinMessage(Event):
    event: Literal["message.unpin.event"]
    chat_id: str
    message_id: str


class PositionChat(Event):
    event: Literal["chat.position.event"]
    chat_id: str
    position: int | None = None
