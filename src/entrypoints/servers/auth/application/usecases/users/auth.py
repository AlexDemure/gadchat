from src.application.collections import UserNotFound
from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.security.jwt import jwt
from src.infrastructure.security.jwt.models import Token


class Repository:
    def __init__(self, session: Session) -> None:
        self.user = adapters.repositories.User(session)


class Security:
    def __init__(self) -> None:
        self.jwt = jwt


class Container:
    def __init__(self, repository: Repository, security: Security) -> None:
        self.repository = repository
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def execute(self, user_id: str) -> Token:
        try:
            user = await self.container.repository.user.one(Filter.eq(key="external_id", value=user_id))
        except UserNotFound:
            user = await self.container.repository.user.create(
                {
                    "id": uuid.unique(),
                    "external_id": user_id,
                    "authorization": date.now(),
                    "options": {},
                },
            )
        return self.container.security.jwt.encode(subject=user.id)
