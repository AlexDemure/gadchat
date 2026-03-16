from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from src.application.usecases.users.jwt import Usecase
from src.entrypoints.http.public.deps.users.jwt import dependency
from src.infrastructure.databases.postgres.tables import User


async def user(
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer(bearerFormat="JWT")),
    usecase: Usecase = Depends(dependency),
) -> User:
    return await usecase(authorization.credentials)
