from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from .base import Command


class CreateChat(Command):
    class Payload(BaseModel):
        title: str | None = None
        user_ids: list[str] = Field(default_factory=list, alias="users")

    topic: Literal["chat.create.command"]
    payload: Payload


class PositionChat(Command):
    class Payload(BaseModel):
        chat_id: str
        position: int | None = None

    topic: Literal["chat.position.command"]
    payload: Payload


class CreateMessage(Command):
    class Payload(BaseModel):
        class Reply(BaseModel):
            message_id: str | None = Field(default=None, alias="message")

        class Forward(BaseModel):
            message_id: str | None = Field(default=None, alias="message")
            chat_id: str | None = Field(default=None, alias="chat")

        chat_id: str
        text: str | None = None
        file_ids: list[str] = Field(default_factory=list, alias="files")
        reply: Reply | None = None
        forward: Forward | None = None

    topic: Literal["message.create.command"]
    payload: Payload


class PinMessage(Command):
    class Payload(BaseModel):
        chat_id: str
        message_id: str

    topic: Literal["message.pin.command"]
    payload: Payload


class UnpinMessage(Command):
    class Payload(BaseModel):
        chat_id: str
        message_id: str

    topic: Literal["message.unpin.command"]
    payload: Payload


class ReadMessage(Command):
    class Payload(BaseModel):
        chat_id: str
        message_id: str

    topic: Literal["message.read.command"]
    payload: Payload
