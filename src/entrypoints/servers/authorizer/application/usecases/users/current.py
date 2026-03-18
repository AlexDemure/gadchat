from src.decorators import sessionmaker
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
    def __init__(self) -> None:
        self.container = None

    def build(self, session: Session) -> None:
        self.container = Container(repository=Repository(session), security=Security())

    @sessionmaker.read
    async def execute(self, session: Session, token: str) -> User:
        self.build(session)

        token = self.container.security.jwt.decode(token=token)

        user = await self.container.repository.user.one(Filter.eq(key="id", value=token.sub))

        return user
