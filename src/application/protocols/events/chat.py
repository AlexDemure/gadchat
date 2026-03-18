import typing

from pydantic import BaseModel

from src.application.protocols.domain.chat import Chat
from src.application.protocols.transport import Event
from src.infrastructure.brokers.collections import EventKind
from src.infrastructure.brokers.collections import EventStatus
from src.infrastructure.brokers.collections import Topic


class CreateChat(Event):
    class Payload(BaseModel):
        chat: Chat

    kind: typing.Literal[EventKind.event] = EventKind.event
    status: typing.Literal[EventStatus.completed] = EventStatus.completed
    topic: typing.Literal[Topic.chat_create] = Topic.chat_create
    payload: Payload
