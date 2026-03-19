from pydantic import BaseModel

from src.application.protocols.domain.chat import Chat
from src.application.protocols.transport.event import Event


class CreateChat(Event):
    class Response(BaseModel):
        chat: Chat

    response: Response
