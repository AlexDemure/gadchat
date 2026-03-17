from src.application.collections import MessageKind
from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import Chat
from src.infrastructure.databases.postgres.tables import Event
from src.infrastructure.databases.postgres.tables import User


TOPIC_CHAT_CREATE = "chat.create.command"


class Repository:
    def __init__(self, session: Session) -> None:
        self.role = adapters.repositories.Role(session)
        self.user = adapters.repositories.User(session)
        self.chat = adapters.repositories.Chat(session)
        self.event = adapters.repositories.Event(session)
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)


class Container:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    def normalize(self, user: User, title: str, user_ids: list[str]) -> tuple[str | None, list[str]]:
        normalized_title = title.strip() or None
        normalized_user_ids: list[str] = []

        for user_id in user_ids:
            if user_id == user.id:
                continue
            if user_id in normalized_user_ids:
                continue
            normalized_user_ids.append(user_id)

        return normalized_title, normalized_user_ids

    async def validate(self, user: User, title: str, user_ids: list[str]) -> tuple[str | None, list[str]]:
        normalized_title, normalized_user_ids = self.normalize(user=user, title=title, user_ids=user_ids)

        await self.container.repository.role.one(Filter.eq(key="id", value="admin"))
        await self.container.repository.role.one(Filter.eq(key="id", value="customer"))

        for user_id in normalized_user_ids:
            await self.container.repository.user.one(Filter.eq(key="id", value=user_id))

        return normalized_title, normalized_user_ids

    async def execute(self, user: User, title: str, user_ids: list[str], chat_id: str | None = None) -> Chat:
        title, user_ids = await self.validate(user=user, title=title, user_ids=user_ids)

        if chat_id and await self.container.repository.chat.exists(Filter.eq(key="id", value=chat_id)):
            return await self.container.repository.chat.relations(Filter.eq(key="id", value=chat_id))

        admin = await self.container.repository.role.one(Filter.eq(key="id", value="admin"))
        customer = await self.container.repository.role.one(Filter.eq(key="id", value="customer"))

        created = date.now()

        chat = await self.container.repository.chat.create(
            {
                "id": chat_id or uuid.unique(),
                "title": title,
                "options": {},
                "created": created,
            },
        )

        await self.container.repository.member.create(
            {
                "id": uuid.unique(),
                "chat_id": chat.id,
                "user_id": user.id,
                "role_id": admin.id,
                "position": None,
                "notifications": 0,
            }
        )

        for user_id in user_ids:
            await self.container.repository.member.create(
                {
                    "id": uuid.unique(),
                    "chat_id": chat.id,
                    "user_id": user_id,
                    "role_id": customer.id,
                    "position": None,
                    "notifications": 0,
                }
            )

        await self.container.repository.message.create(
            {
                "id": uuid.unique(),
                "chat_id": chat.id,
                "user_id": None,
                "member_id": None,
                "kind": MessageKind.system.value,
                "text": "Канал создан",
                "created": created,
            }
        )

        chat = await self.container.repository.chat.relations(Filter.eq(key="id", value=chat.id))

        return chat

    async def publish(self, user: User, title: str, user_ids: list[str]) -> Event:
        title, user_ids = await self.validate(user=user, title=title, user_ids=user_ids)
        created = date.now()
        return await self.container.repository.event.create(
            {
                "id": uuid.unique(),
                "topic": TOPIC_CHAT_CREATE,
                "priority": 100,
                "payload": {
                    "user_id": user.id,
                    "chat_id": uuid.unique(),
                    "title": title,
                    "user_ids": user_ids,
                },
                "created": created,
                "dispatched": None,
                "completed": None,
                "failed": None,
                "error": None,
            }
        )
