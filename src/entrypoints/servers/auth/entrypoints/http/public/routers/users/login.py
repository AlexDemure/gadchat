from fastapi import Depends
from fastapi import Header
from fastapi import status

from src.entrypoints.servers.auth.application.usecases.users.login import Usecase
from src.entrypoints.servers.auth.entrypoints.http.public.deps.users.login import dependency
from src.framework.routing import APIRouter
from src.infrastructure.security.jwt.models import Token


router = APIRouter()


@router.post(
    "/api/users:login",
    status_code=status.HTTP_201_CREATED,
    response_model=Token,
    responses={status.HTTP_401_UNAUTHORIZED: {}},
    description="Login",
)
async def command(
    user_id: str = Header(alias="x-user-id"),
    usecase: Usecase = Depends(dependency),
) -> Token:
    return await usecase.execute(user_id=user_id)
