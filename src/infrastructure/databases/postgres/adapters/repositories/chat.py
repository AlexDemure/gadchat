import datetime
import typing

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


class Member(Base[crud.Member, tables.Member, exceptions.MemberNotFound]):
    crud = crud.Member
    table = tables.Member
    error = exceptions.MemberNotFound

    async def user_ids(self, chat_id: str, shard_id: int | None = None) -> list[str]:
        return await self.crud.user_ids(self.session, chat_id=chat_id, shard_id=shard_id)

    async def users(self, chat_id: str, shard_id: int | None = None) -> list[dict[str, typing.Any]]:
        return await self.crud.users(self.session, chat_id=chat_id, shard_id=shard_id)

    async def user(self, chat_id: str, user_id: str) -> tables.Member | None:
        return await self.crud.user(self.session, chat_id=chat_id, user_id=user_id)

    async def mark_read(
        self,
        chat_member_id: str,
        message_id: str,
        read: datetime.datetime,
        unread_count: int,
    ) -> None:
        await self.crud.mark_read(
            self.session,
            chat_member_id=chat_member_id,
            message_id=message_id,
            read=read,
            unread_count=unread_count,
        )

    async def increment_unread(self, chat_id: str, shard_id: int | None, excluded_chat_member_id: str) -> None:
        await self.crud.increment_unread(
            self.session,
            chat_id=chat_id,
            shard_id=shard_id,
            excluded_chat_member_id=excluded_chat_member_id,
        )

    async def pin(self, member_id: str, user_id: str) -> None:
        await self.crud.pin(self.session, member_id=member_id, user_id=user_id)

    async def unpin(self, member_id: str, user_id: str) -> None:
        await self.crud.unpin(self.session, member_id=member_id, user_id=user_id)

    async def reorder(self, user_id: str, chat_ids: list[str]) -> None:
        await self.crud.reorder(self.session, user_id=user_id, chat_ids=chat_ids)


class Message(Base[crud.Message, tables.Message, exceptions.MessageNotFound]):
    crud = crud.Message
    table = tables.Message
    error = exceptions.MessageNotFound

    async def duplicate(self, *filters: typing.Union[Filter, And, Or]) -> tables.Message | None:
        return await self.crud.duplicate(self.session, *filters)

    async def latest(self, *filters: typing.Union[Filter, And, Or]) -> tables.Message | None:
        return await self.crud.latest(self.session, *filters)

    async def pin(self, message_id: str, chat_id: str) -> None:
        await self.crud.pin(self.session, message_id=message_id, chat_id=chat_id)

    async def unpin(self, message_id: str, chat_id: str) -> None:
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


class Attachment(Base[crud.Attachment, tables.Attachment, exceptions.AttachmentNotFound]):
    crud = crud.Attachment
    table = tables.Attachment
    error = exceptions.AttachmentNotFound

    async def exists_in_chat(self, chat_id: str, file_id: str) -> bool:
        return await self.crud.exists_in_chat(self.session, chat_id=chat_id, file_id=file_id)


class Reply(Base[crud.Reply, tables.Reply, exceptions.ReplyNotFound]):
    crud = crud.Reply
    table = tables.Reply
    error = exceptions.ReplyNotFound


class Forward(
    Base[crud.Forward, tables.Forward, exceptions.ForwardNotFound]
):
    crud = crud.Forward
    table = tables.Forward
    error = exceptions.ForwardNotFound


class Read(Base[crud.Read, tables.Read, exceptions.ReadNotFound]):
    crud = crud.Read
    table = tables.Read
    error = exceptions.ReadNotFound

    async def mark(
        self,
        member: tables.Member,
        message: tables.Message,
        read: datetime.datetime,
    ) -> int:
        return await self.crud.mark(
            self.session,
            chat_member=member,
            message=message,
            read=read,
        )
