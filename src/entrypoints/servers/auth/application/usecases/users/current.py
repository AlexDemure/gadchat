from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import User
from src.infrastructure.security.jwt import jwt


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

    async def execute(self, token: str) -> User:
        return await self.container.repository.user.one(
            Filter.eq(
                key="id",
                value=self.container.security.jwt.decode(token=token).sub,
            )
        )
