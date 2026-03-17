from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from src.entrypoints.servers.auth.application.usecases.users.current import Usecase
from src.entrypoints.servers.auth.entrypoints.http.public.deps.users.current import dependency as usecase
from src.infrastructure.databases.postgres.tables import User


async def dependency(
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer(bearerFormat="JWT")),
    _usecase: Usecase = Depends(usecase),
) -> User:
    return await _usecase.execute(authorization.credentials)
