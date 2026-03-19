from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from src.application.protocols.transport.event import Event


class CreateChat(Event):
    class Payload(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        title: str | None = None
        user_ids: list[str] = Field(default_factory=list, alias="users")

    user_id: str
    payload: Payload


class CreateMessage(Event):
    class Payload(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        class Reply(BaseModel):
            model_config = ConfigDict(populate_by_name=True)

            message_id: str = Field(alias="message")

        class Forward(BaseModel):
            model_config = ConfigDict(populate_by_name=True)

            chat_id: str = Field(alias="chat")
            message_id: str = Field(alias="message")

        chat_id: str = Field(alias="chat")
        text: str | None = None
        reply: Reply | None = None
        forward: Forward | None = None
        file_ids: list[str] = Field(default_factory=list, alias="files")

    user_id: str
    payload: Payload
