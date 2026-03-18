from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.decorators import sessionmaker
from src.domain.collections import MessageKind
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import Chat
from src.infrastructure.databases.postgres.tables import User


class Repository:
    def __init__(self, session: Session) -> None:
        self.role = adapters.repositories.Role(session)
        self.user = adapters.repositories.User(session)
        self.chat = adapters.repositories.Chat(session)
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)


class Container:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


class Usecase:
    def __init__(self) -> None:
        self.container = None

    def build(self, session: Session) -> None:
        self.container = Container(repository=Repository(session))

    @sessionmaker.write
    async def execute(self, session: Session, user: User, title: str, user_ids: list[str]) -> Chat:
        self.build(session)
        admin = await self.container.repository.role.one(Filter.eq(key="id", value="admin"))
        customer = await self.container.repository.role.one(Filter.eq(key="id", value="customer"))

        created = date.now()

        chat = await self.container.repository.chat.create(
            {
                "id": uuid.unique(),
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

        return await self.container.repository.chat.relations(Filter.eq(key="id", value=chat.id))
