import typing

from pydantic import BaseModel
from pydantic import Field

from src.common.typings.validators import Search
from src.entrypoints.http.common.schemas import Paginated
from src.entrypoints.http.common.schemas import Pagination
from src.infrastructure.databases.postgres.tables import Chat as _Chat
from src.infrastructure.databases.postgres.tables import Message as _Message
from src.infrastructure.databases.postgres.tables import User as _User
from src.protocols.chat import Chat
from src.protocols.chat import Message


class SearchChats(BaseModel):
    class Filters(BaseModel):
        text: Search | None = None

    class CursorPagination(Pagination): ...

    filters: Filters = Field(default_factory=Filters)
    pagination: CursorPagination = Field(default_factory=CursorPagination)

    def deserialize(self) -> dict[str, typing.Any]:
        return self.model_dump()


class SearchMessages(BaseModel):
    class Filters(BaseModel):
        text: Search | None = None

    class CursorPagination(Pagination): ...

    filters: Filters = Field(default_factory=Filters)
    pagination: CursorPagination = Field(default_factory=CursorPagination)

    def deserialize(self) -> dict[str, typing.Any]:
        return self.model_dump()


class Chats(Paginated, BaseModel):
    items: list[Chat]

    @classmethod
    def serialize(
        cls,
        user: _User,
        chats: list[_Chat],
        more: bool,
        prev: str | None,
        next: str | None,
    ) -> typing.Self:
        return cls(
            items=[Chat.serialize(user=user, chat=chat) for chat in chats],
            more=more,
            prev=prev,
            next=next,
        )


class Messages(Paginated, BaseModel):
    items: list[Message]

    @classmethod
    def serialize(
        cls,
        messages: list[_Message],
        more: bool,
        prev: str | None,
        next: str | None,
    ) -> typing.Self:
        return cls(
            items=[Message.serialize(message) for message in messages],
            more=more,
            prev=prev,
            next=next,
        )
