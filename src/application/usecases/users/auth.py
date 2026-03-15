from src.infrastructure.security.jwt import jwt
from src.infrastructure.security.jwt.client import JWT
from src.infrastructure.security.jwt.models import Token


class Repositories:
    def __init__(self) -> None: ...


class Security:
    def __init__(self) -> None:
        self.jwt: JWT = jwt


class Container:
    def __init__(self, repositories: Repositories, security: Security) -> None:
        self.repositories = repositories
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def __call__(self, user_id: str) -> Token:
        return self.container.security.jwt.encode(user_id)
