import typing

from pydantic import Field

from src.application.protocols.domain import Chat
from src.application.protocols.domain import Message
from src.common.typings.validators import Search
from src.entrypoints.http.common.schemas import Paginated
from src.entrypoints.http.common.schemas import Pagination
from src.entrypoints.http.common.schemas import Query
from src.entrypoints.http.common.schemas import Request
from src.entrypoints.http.common.schemas import Response
from src.infrastructure.databases.postgres.tables import Chat as _Chat
from src.infrastructure.databases.postgres.tables import Message as _Message
from src.infrastructure.databases.postgres.tables import User as _User

from .base import Public


class SearchChats(Public, Request, Query):
    class SearchChatsFilters(Public, Request, Query):
        text: Search | None = None

    class SearchChatsPagination(Public, Request, Query, Pagination): ...

    filters: SearchChatsFilters = Field(default_factory=SearchChatsFilters)
    pagination: SearchChatsPagination = Field(default_factory=SearchChatsPagination)


class SearchMessages(Public, Request, Query):
    class SearchMessagesFilters(Public, Request, Query):
        text: Search | None = None

    class SearchMessagesPagination(Public, Request, Query, Pagination): ...

    filters: SearchMessagesFilters = Field(default_factory=SearchMessagesFilters)
    pagination: SearchMessagesPagination = Field(default_factory=SearchMessagesPagination)


class Messages(Public, Response, Paginated):
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


class Chats(Public, Response, Paginated):
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
            more=more,
            prev=prev,
            next=next,
            items=[Chat.serialize(user=user, chat=chat) for chat in chats],
        )
