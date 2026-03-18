import enum


class EventKind(enum.StrEnum):
    command = "command"
    event = "event"


class EventStatus(enum.StrEnum):
    request = "request"
    accepted = "accepted"
    completed = "completed"
    error = "error"
