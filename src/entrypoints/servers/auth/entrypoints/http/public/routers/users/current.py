from fastapi import Depends
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.servers.auth.application.usecases.users.current import Usecase
from src.entrypoints.servers.auth.entrypoints.http.public.deps.users.current import dependency
from src.entrypoints.servers.auth.entrypoints.http.public.schemas import User
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.get(
    "/api/users:current",
    status_code=status.HTTP_200_OK,
    response_model=User,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Current user",
)
async def query(
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer(bearerFormat="JWT")),
    usecase: Usecase = Depends(dependency),
) -> User:
    return User.serialize(await usecase.execute(authorization.credentials))
