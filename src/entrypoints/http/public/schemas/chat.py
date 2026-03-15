import typing

from pydantic import BaseModel
from pydantic import Field

from src.infrastructure.databases.postgres.tables import Chat
from src.infrastructure.databases.postgres.tables import File
from src.infrastructure.databases.postgres.tables import Message
from src.infrastructure.databases.postgres.tables import MessageFile


class CreateMessage(BaseModel):
    chat_id: str | None = None
    peer_user_id: str | None = None
    body: str = ""
    attachments: list[dict[str, typing.Any]] = Field(default_factory=list)


class Attachment(BaseModel):
    id: str
    storage: str
    bucket: str
    key: str
    filename: str | None
    content_type: str | None
    size_bytes: int | None
    position: int

    @classmethod
    def serialize(cls, row: MessageFile) -> typing.Self:
        return cls(
            id=str(row.file.id),
            storage=row.file.storage,
            bucket=row.file.bucket,
            key=row.file.key,
            filename=row.file.filename,
            content_type=row.file.content_type,
            size_bytes=row.file.size_bytes,
            position=row.position,
        )


class UploadedFile(BaseModel):
    id: str
    storage: str
    bucket: str
    key: str
    filename: str | None
    content_type: str | None
    size_bytes: int | None

    @classmethod
    def serialize(cls, row: File) -> typing.Self:
        return cls(
            id=str(row.id),
            storage=row.storage,
            bucket=row.bucket,
            key=row.key,
            filename=row.filename,
            content_type=row.content_type,
            size_bytes=row.size_bytes,
        )


class ChatMessage(BaseModel):
    id: str
    chat_id: str
    sender_id: str
    member_id: str
    body: str | None
    attachments: list[Attachment]
    created: str

    @classmethod
    def serialize(cls, row: Message) -> typing.Self:
        return cls(
            id=str(row.id),
            chat_id=str(row.chat_id),
            sender_id=row.member.user_id,
            member_id=str(row.member_id),
            body=row.body,
            attachments=[Attachment.serialize(attachment) for attachment in row.attachments],
            created=row.created.isoformat(),
        )


class MessageCommand(BaseModel):
    status: str
    chat_id: str | None = None
    message: ChatMessage | None = None


class MessagePage(BaseModel):
    items: list[ChatMessage]
    has_more: bool
    prev_cursor: str | None
    next_cursor: str | None

    @classmethod
    def serialize(
        cls,
        *,
        items: list[Message],
        has_more: bool,
        prev_cursor: str | None,
        next_cursor: str | None,
    ) -> typing.Self:
        return cls(
            items=[ChatMessage.serialize(item) for item in items],
            has_more=has_more,
            prev_cursor=prev_cursor,
            next_cursor=next_cursor,
        )


class MessageCreated(BaseModel):
    event: str
    chat_id: str
    message: ChatMessage
    recipients: list[str]

    @classmethod
    def serialize(
        cls,
        *,
        chat_id: str,
        message: Message,
        recipients: list[str],
    ) -> dict[str, typing.Any]:
        return cls(
            event="message.created",
            chat_id=chat_id,
            message=ChatMessage.serialize(message),
            recipients=recipients,
        ).model_dump()


class ChatItem(BaseModel):
    chat_id: str
    kind: str
    title: str | None
    members: list[str]
    last_message_preview: str | None
    last_message_at: str | None

    @classmethod
    def serialize(
        cls,
        *,
        chat: Chat,
        members: list[str],
        last_message: Message | None,
    ) -> typing.Self:
        return cls(
            chat_id=str(chat.id),
            kind=chat.kind,
            title=chat.title,
            members=members,
            last_message_preview=last_message.body if last_message else None,
            last_message_at=last_message.created.isoformat() if last_message and last_message.created else None,
        )


class Chats(BaseModel):
    items: list[ChatItem]

    @classmethod
    def serialize(cls, items: list[dict[str, typing.Any]]) -> typing.Self:
        return cls(
            items=[
                ChatItem.serialize(
                    chat=item["chat"],
                    members=item["members"],
                    last_message=item["last_message"],
                )
                for item in items
            ]
        )
