from pydantic import BaseModel

from src.application.protocols.domain.chat import Chat
from src.application.protocols.domain.chat import Message
from src.application.protocols.transport.event import Event


class CreateChat(Event):
    class Response(BaseModel):
        chat: Chat

    response: Response


class CreateMessage(Event):
    class Response(BaseModel):
        message: Message

    response: Response
