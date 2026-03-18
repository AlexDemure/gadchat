import enum


class MessageKind(str, enum.Enum):
    system = "system"
    user = "user"
