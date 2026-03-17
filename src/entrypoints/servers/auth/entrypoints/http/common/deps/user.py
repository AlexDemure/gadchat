from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from src.entrypoints.servers.auth.application.usecases.users.current import Usecase
from src.entrypoints.servers.auth.entrypoints.http.public.deps.users.current import dependency
from src.infrastructure.databases.postgres.tables import User


async def user(
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer(bearerFormat="JWT")),
    usecase: Usecase = Depends(dependency),
) -> User:
    return await usecase.execute(authorization.credentials)
