from src.infrastructure.security.jwt import jwt


class Repository:
    def __init__(self) -> None: ...


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

    async def __call__(self, token: str) -> str:
        return self.container.security.jwt.decode(token=token).sub
