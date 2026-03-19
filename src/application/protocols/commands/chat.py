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
