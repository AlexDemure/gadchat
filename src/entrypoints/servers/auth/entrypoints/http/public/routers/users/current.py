from fastapi import Depends
from fastapi import status

from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.entrypoints.servers.auth.entrypoints.http.public.schemas import User
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter
from src.infrastructure.databases.postgres.tables import User as _User


router = APIRouter()


@router.get(
    "/api/users:current",
    status_code=status.HTTP_200_OK,
    response_model=User,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Current user",
)
async def query(_user: _User = Depends(user)) -> User:
    return User.serialize(_user)
