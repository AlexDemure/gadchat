import datetime
import typing
import uuid

from src.application.collections import exceptions
from src.infrastructure.databases.orm.sqlalchemy.models import And
from src.infrastructure.databases.orm.sqlalchemy.models import Filter
from src.infrastructure.databases.orm.sqlalchemy.models import Or
from src.infrastructure.databases.postgres import crud
from src.infrastructure.databases.postgres import tables

from .base import Base


class Chat(Base[crud.Chat, tables.Chat, exceptions.ChatNotFound]):
    crud = crud.Chat
    table = tables.Chat
    error = exceptions.ChatNotFound

    async def direct(self, user_a: str, user_b: str) -> tables.Chat | None:
        return await self.crud.direct(self.session, user_a=user_a, user_b=user_b)

    async def search(
        self,
        filters: dict[str, typing.Any],
        sorting: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> dict[str, typing.Any]:
        return await self.crud.search(
            self.session,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

class Member(Base[crud.Member, tables.Member, Exception]):
    crud = crud.Member
    table = tables.Member
    error = Exception

    async def ensure(self, user_id: str, created: datetime.datetime) -> tables.Member:
        return await self.crud.ensure(self.session, user_id=user_id, created=created)

    async def by_user_id(self, user_id: str) -> tables.Member | None:
        return await self.crud.by_user_id(self.session, user_id=user_id)


class ChatMember(Base[crud.ChatMember, tables.ChatMember, exceptions.ChatMemberRequired]):
    crud = crud.ChatMember
    table = tables.ChatMember
    error = exceptions.ChatMemberRequired

    async def user_ids(self, chat_id: uuid.UUID, shard_id: int) -> list[str]:
        return await self.crud.user_ids(self.session, chat_id=chat_id, shard_id=shard_id)

    async def users(self, chat_id: uuid.UUID, shard_id: int) -> list[dict[str, typing.Any]]:
        return await self.crud.users(self.session, chat_id=chat_id, shard_id=shard_id)

    async def user(self, chat_id: uuid.UUID, user_id: str) -> tables.ChatMember | None:
        return await self.crud.user(self.session, chat_id=chat_id, user_id=user_id)

    async def mark_read(self, chat_member_id: uuid.UUID, read_at: datetime.datetime) -> None:
        await self.crud.mark_read(self.session, chat_member_id=chat_member_id, read_at=read_at)


class Message(Base[crud.Message, tables.Message, exceptions.MessageNotFound]):
    crud = crud.Message
    table = tables.Message
    error = exceptions.MessageNotFound

    async def duplicate(self, *filters: typing.Union[Filter, And, Or]) -> tables.Message | None:
        return await self.crud.duplicate(self.session, *filters)

    async def latest(self, *filters: typing.Union[Filter, And, Or]) -> tables.Message | None:
        return await self.crud.latest(self.session, *filters)

    async def pin(self, message_id: uuid.UUID, chat_id: uuid.UUID) -> None:
        await self.crud.pin(self.session, message_id=message_id, chat_id=chat_id)

    async def unpin(self, message_id: uuid.UUID, chat_id: uuid.UUID) -> None:
        await self.crud.unpin(self.session, message_id=message_id, chat_id=chat_id)

    async def search(
        self,
        filters: dict[str, typing.Any],
        sorting: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> dict[str, typing.Any]:
        return await self.crud.search(
            self.session,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )


class MessageFile(Base[crud.MessageFile, tables.MessageFile, exceptions.FileNotFound]):
    crud = crud.MessageFile
    table = tables.MessageFile
    error = exceptions.FileNotFound


class ChatPin(Base[crud.ChatPin, tables.ChatPin, Exception]):
    crud = crud.ChatPin
    table = tables.ChatPin
    error = Exception

    async def pin(self, chat_member_id: uuid.UUID, user_id: str) -> None:
        await self.crud.pin(self.session, chat_member_id=chat_member_id, user_id=user_id)

    async def unpin(self, chat_member_id: uuid.UUID, user_id: str) -> None:
        await self.crud.unpin(self.session, chat_member_id=chat_member_id, user_id=user_id)

    async def reorder(self, user_id: str, chat_ids: list[uuid.UUID]) -> None:
        await self.crud.reorder(self.session, user_id=user_id, chat_ids=chat_ids)


class MessageRead(Base[crud.MessageRead, tables.MessageRead, Exception]):
    crud = crud.MessageRead
    table = tables.MessageRead
    error = Exception

    async def mark(
        self,
        chat_member: tables.ChatMember,
        message: tables.Message,
        read_at: datetime.datetime,
    ) -> int:
        return await self.crud.mark(
            self.session,
            chat_member=chat_member,
            message=message,
            read_at=read_at,
        )
