import typing

from pydantic import BaseModel
from pydantic import Field

from src.infrastructure.brokers.collections import EventKind
from src.infrastructure.brokers.collections import EventStatus
from src.infrastructure.brokers.collections import Topic


class Targets(BaseModel):
    user_ids: list[str] = Field(default_factory=list)


class Event(BaseModel):
    request_id: str
    kind: EventKind
    status: EventStatus
    topic: Topic
    targets: Targets | None = None
    payload: dict[str, typing.Any] | None = None
    response: dict[str, typing.Any] | None = None
    error: str | None = None
