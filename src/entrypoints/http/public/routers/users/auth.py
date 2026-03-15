from fastapi import Depends
from fastapi import status

from src.application.usecases.users.auth import Usecase
from src.entrypoints.http.common.deps import header
from src.entrypoints.http.public.deps.users.auth import dependency
from src.framework.routing import APIRouter
from src.infrastructure.security.jwt.models import Token


router = APIRouter()


@router.post(
    "/users:auth",
    status_code=status.HTTP_200_OK,
    response_model=Token,
    responses={status.HTTP_401_UNAUTHORIZED: {}},
    description="Issue an application JWT for chat access",
)
async def command(
    uid: str = Depends(header),
    usecase: Usecase = Depends(dependency),
) -> Token:
    return await usecase(uid)
