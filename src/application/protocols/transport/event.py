import typing

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from src.infrastructure.brokers.collections import EventKind
from src.infrastructure.brokers.collections import EventStatus
from src.infrastructure.brokers.collections import Topic


class Event(BaseModel):
    class Targets(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        user_ids: list[str] = Field(default_factory=list, alias="users")

    request_id: str
    kind: EventKind
    status: EventStatus
    topic: Topic
    targets: Targets | None = None
    payload: typing.Any | None = None
    response: typing.Any | None = None
    error: str | None = None
