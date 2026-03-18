import typing

from src.domain.collections import exceptions
from src.infrastructure.databases.postgres import crud
from src.infrastructure.databases.postgres import tables

from .base import Base


class Chat(Base[crud.Chat, tables.Chat, exceptions.ChatNotFound]):
    crud = crud.Chat
    table = tables.Chat
    error = exceptions.ChatNotFound

    async def search(
        self,
        filters: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> tuple[list[tables.Chat], bool, str | None, str | None]:
        return await self.crud.search(
            self.session,
            filters=filters,
            pagination=pagination,
        )


class Member(Base[crud.Member, tables.Member, exceptions.MemberNotFound]):
    crud = crud.Member
    table = tables.Member
    error = exceptions.MemberNotFound


class Message(Base[crud.Message, tables.Message, exceptions.MessageNotFound]):
    crud = crud.Message
    table = tables.Message
    error = exceptions.MessageNotFound

    async def search(
        self,
        filters: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> tuple[list[tables.Message], bool, str | None, str | None]:
        return await self.crud.search(
            self.session,
            filters=filters,
            pagination=pagination,
        )


class Attachment(Base[crud.Attachment, tables.Attachment, exceptions.AttachmentNotFound]):
    crud = crud.Attachment
    table = tables.Attachment
    error = exceptions.AttachmentNotFound


class Reply(Base[crud.Reply, tables.Reply, exceptions.ReplyNotFound]):
    crud = crud.Reply
    table = tables.Reply
    error = exceptions.ReplyNotFound


class Forward(Base[crud.Forward, tables.Forward, exceptions.ForwardNotFound]):
    crud = crud.Forward
    table = tables.Forward
    error = exceptions.ForwardNotFound


class Read(Base[crud.Read, tables.Read, exceptions.ReadNotFound]):
    crud = crud.Read
    table = tables.Read
    error = exceptions.ReadNotFound
