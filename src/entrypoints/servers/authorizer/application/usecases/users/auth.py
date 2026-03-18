from src.common.formats.utils import date
from src.decorators import sessionmaker
from src.domain.collections import UserNotFound
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
    def __init__(self) -> None:
        self.container = None

    def build(self, session: Session) -> None:
        self.container = Container(repository=Repository(session), security=Security())

    @sessionmaker.write
    async def execute(self, session: Session, user_id: str) -> Token:
        self.build(session)

        try:
            user = await self.container.repository.user.one(Filter.eq(key="id", value=user_id))
        except UserNotFound:
            user = await self.container.repository.user.create(
                {
                    "id": user_id,
                    "authorization": date.now(),
                    "options": {},
                },
            )

        token = self.container.security.jwt.encode(subject=user.id)

        return token
