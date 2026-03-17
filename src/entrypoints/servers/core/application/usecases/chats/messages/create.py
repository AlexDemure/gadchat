from src.application.collections import MessageKind
from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.infrastructure.databases.orm.sqlalchemy.queries import And
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import User


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat = adapters.repositories.Chat(session)
        self.file = adapters.repositories.File(session)
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)
        self.attachment = adapters.repositories.Attachment(session)
        self.forward = adapters.repositories.Forward(session)
        self.reply = adapters.repositories.Reply(session)


class Container:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def __call__(
        self,
        user: User,
        chat_id: str,
        text: str | None,
        reply: dict[str, str] | None,
        forward: dict[str, str] | None,
        file_ids: list[str],
    ) -> None:
        chat = await self.container.repository.chat.one(Filter.eq(key="id", value=chat_id))

        member = await self.container.repository.member.one(
            And.combine(
                Filter.eq(key="chat_id", value=chat.id),
                Filter.eq(key="user_id", value=user.id),
            )
        )

        message = await self.container.repository.message.create(
            {
                "id": uuid.unique(),
                "chat_id": chat.id,
                "user_id": user.id,
                "member_id": member.id,
                "kind": MessageKind.user,
                "text": text,
                "pinned": None,
                "edited": None,
                "created": date.now(),
            },
        )

        for file_id in file_ids:
            file = await self.container.repository.file.one(Filter.eq(key="id", value=file_id))
            await self.container.repository.attachment.create(
                {
                    "id": uuid.unique(),
                    "message_id": message.id,
                    "file_id": file.id,
                },
            )

        if reply:
            await self.container.repository.reply.create(
                {
                    "id": uuid.unique(),
                    "message_id": message.id,
                    "source_message_id": reply["message_id"],
                    "created": date.now(),
                },
            )

        if forward:
            await self.container.repository.forward.create(
                {
                    "id": uuid.unique(),
                    "message_id": message.id,
                    "source_message_id": forward["message_id"],
                    "created": date.now(),
                },
            )

        members = await self.container.repository.member.all(Filter.eq(key="chat_id", value=chat.id))

        for _member in members:
            if _member.id != member.id:
                await self.container.repository.member.update(id=_member.id, notifications=_member.notifications + 1)
