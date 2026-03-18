from pydantic import BaseModel
from pydantic import Field

from src.application.protocols.transport import Event


class CreateChat(Event):
    class Payload(BaseModel):
        title: str | None = None
        user_ids: list[str] = Field(default_factory=list, alias="users")

    user_id: str
    payload: Payload
