from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from src.application.usecases.users.get import Usecase
from src.entrypoints.http.public.deps.users.get import dependency
from src.infrastructure.security.jwt.collections import TokenInvalid


async def jwt(
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer(bearerFormat="JWT")),
    usecase: Usecase = Depends(dependency),
) -> str:
    try:
        return await usecase(authorization.credentials)
    except TokenInvalid as exc:
        raise HTTPException(status_code=401, detail="Invalid authorization token") from exc
