import typing

from pydantic import Field

from src.common.typings.validators import Search
from src.common.typings.validators import String
from src.common.typings.validators import StrRef
from src.configuration import settings
from src.entrypoints.http.common.schemas import Command
from src.entrypoints.http.common.schemas import Paginated
from src.entrypoints.http.common.schemas import Pagination
from src.entrypoints.http.common.schemas import Query
from src.entrypoints.http.common.schemas import Request
from src.entrypoints.http.common.schemas import Response
from src.infrastructure.databases.orm.sqlalchemy.collections import Direction
from src.infrastructure.databases.postgres.tables import Chat as _Chat
from src.infrastructure.databases.postgres.tables import File as _File
from src.infrastructure.databases.postgres.tables import Message as _Message

from .base import Public


class CreateMessage(Public, Request, Command):
    class Reply(Public, Request, Command):
        message_id: StrRef = Field(alias="message")

    class Forward(Public, Request, Command):
        chat_id: StrRef = Field(alias="chat")
        message_id: StrRef = Field(alias="message")

    text: String | None = None
    reply: Reply | None = None
    forward: Forward | None = None
    file_ids: list[StrRef] = Field(default_factory=list, alias="files")

    def deserialize(self) -> dict[str, typing.Any]:
        return {
            "text": self.text,
            "reply": self.reply.model_dump() if self.reply is not None else None,
            "forward": self.forward.model_dump() if self.forward is not None else None,
            "file_ids": self.file_ids,
        }


class CreateChat(Public, Request, Command):
    title: String
    user_ids: list[StrRef] = Field(default_factory=list, alias="users")


class PositionChat(Public, Request, Command):
    position: int | None


class SearchChats(Public, Request, Query):
    class SearchChatsFilters(Public, Request, Query):
        text: Search | None = None

    class SearchChatsSorting(Public, Request, Query):
        field: typing.Literal["activity_at"] = "activity"
        direction: Direction = Direction.desc

    class SearchChatsPagination(Public, Request, Query, Pagination): ...

    filters: SearchChatsFilters = Field(default_factory=SearchChatsFilters)
    sorting: SearchChatsSorting = Field(default_factory=SearchChatsSorting)
    pagination: SearchChatsPagination


class SearchMessages(Public, Request, Query):
    class SearchMessagesFilters(Public, Request, Query):
        text: Search | None = None

    class SearchMessagesSorting(Public, Request, Query):
        field: typing.Literal["created"] = "created"
        direction: Direction = Direction.desc

    class SearchMessagesPagination(Public, Request, Query, Pagination): ...

    filters: SearchMessagesFilters = Field(default_factory=SearchMessagesFilters)
    sorting: SearchMessagesSorting = Field(default_factory=SearchMessagesSorting)
    pagination: SearchMessagesPagination


class File(Public, Response):
    id: str
    filename: str | None
    content_type: str | None
    path: str
    url: str

    @classmethod
    def serialize(cls, file: _File) -> typing.Self:
        return cls(
            id=file.id,
            filename=file.filename,
            content_type=file.content_type,
            path=file.path,
            url=f"{settings.MINIO_HOST.rstrip('/')}/{settings.MINIO_BUCKET}{file.path}",
        )


class Message(Public, Response):
    id: str
    text: str | None
    kind: str
    created: str
    pinned: str | None
    author_id: str | None
    files: list[File]

    @classmethod
    def serialize(cls, message: _Message) -> typing.Self:
        return cls(
            id=message.id,
            text=message.text,
            kind=message.kind,
            created=message.created.isoformat(),
            pinned=message.pinned.isoformat() if message.pinned is not None else None,
            author_id=message.user.external_id if message.user is not None else None,
            files=[
                File.serialize(attachment.file)
                for attachment in message.attachments
                if getattr(attachment, "file", None) is not None
            ],
        )


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


class Chat(Public, Response):
    id: str
    title: str | None

    @classmethod
    def serialize(cls, chat: _Chat) -> typing.Self:
        return cls(
            id=chat.id,
            title=chat.title,
        )


class Chats(Public, Response, Paginated):
    items: list[Chat]

    @classmethod
    def serialize(cls, chats: list[_Chat], more: bool, prev: str | None, next: str | None) -> typing.Self:
        return cls(
            more=more,
            prev=prev,
            next=next,
            items=[Chat.serialize(chat) for chat in chats],
        )
