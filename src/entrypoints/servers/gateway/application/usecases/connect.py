from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import Event
from src.infrastructure.databases.postgres.tables import User
from src.protocols.commands import Command


class Repository:
    def __init__(self, session: Session) -> None:
        self.user = adapters.repositories.User(session)
        self.event = adapters.repositories.Event(session)


class Container:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


class Usecase:
    PRIORITY = 100

    def __init__(self, container: Container) -> None:
        self.container = container

    async def user(self, user_id: str) -> User:
        return await self.container.repository.user.one(Filter.eq(key="id", value=user_id))

    async def publish(self, user_id: str, command: Command) -> Event:
        user = await self.user(user_id=user_id)

        payload = command.payload.model_dump(mode="json")
        payload["user_id"] = user.id

        return await self.container.repository.event.create(
            {
                "id": uuid.unique(),
                "topic": command.topic,
                "priority": self.PRIORITY,
                "payload": payload,
                "created": date.now(),
                "dispatched": None,
                "completed": None,
                "failed": None,
                "error": None,
            }
        )
