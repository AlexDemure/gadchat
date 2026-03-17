import typing

from pydantic import BaseModel

from src.common.formats.utils import date


class Event(BaseModel):
    id: str
    topic: str
    created: str
    dispatched: str | None = None
    completed: str | None = None
    failed: str | None = None
    error: str | None = None

    @classmethod
    def serialize(cls, event: typing.Any) -> typing.Self:
        return cls(
            id=event.id,
            topic=event.topic,
            created=event.created.isoformat(),
            dispatched=event.dispatched.isoformat() if event.dispatched else None,
            completed=event.completed.isoformat() if event.completed else None,
            failed=event.failed.isoformat() if event.failed else None,
            error=event.error,
        )

    @classmethod
    def mock(cls, topic: str) -> typing.Self:
        return cls(
            id="pending",
            topic=topic,
            created=date.now().isoformat(),
            dispatched=None,
            completed=None,
            failed=None,
            error=None,
        )
