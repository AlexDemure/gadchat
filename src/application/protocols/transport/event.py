import typing

from pydantic import BaseModel
from pydantic import Field

from src.infrastructure.brokers.collections import EventKind
from src.infrastructure.brokers.collections import EventStatus
from src.infrastructure.brokers.collections import Topic


class Event(BaseModel):
    class Targets(BaseModel):
        user_ids: list[str] = Field(default_factory=list)

    request_id: str
    kind: EventKind
    status: EventStatus
    topic: Topic
    targets: Targets | None = None
    payload: typing.Any | None = None
    response: typing.Any | None = None
    error: str | None = None
