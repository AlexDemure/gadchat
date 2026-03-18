import enum


class Topic(enum.StrEnum):
    chat_create = "chat.create"

    @property
    def command(self) -> str:
        return f"{self.value}.command"

    @property
    def event(self) -> str:
        return f"{self.value}.event"
