import enum


class Topic(enum.StrEnum):
    chat_create = "chat.create"
    chat_position = "chat.position"
    message_create = "message.create"
    message_pin = "message.pin"
    message_unpin = "message.unpin"
    message_read = "message.read"

    @property
    def command(self) -> str:
        return f"{self.value}.command"

    @property
    def event(self) -> str:
        return f"{self.value}.event"
