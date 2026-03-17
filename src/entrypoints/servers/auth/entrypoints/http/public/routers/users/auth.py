from fastapi import Depends
from fastapi import status

from src.entrypoints.servers.auth.application.usecases.users.auth import Usecase
from src.entrypoints.servers.auth.entrypoints.http.common.deps import header
from src.entrypoints.servers.auth.entrypoints.http.public.deps.users.auth import dependency
from src.framework.routing import APIRouter
from src.infrastructure.security.jwt.models import Token


router = APIRouter()


@router.post(
    "/api/users:auth",
    status_code=status.HTTP_201_CREATED,
    response_model=Token,
    responses={status.HTTP_401_UNAUTHORIZED: {}},
    description="Authenticate user",
)
async def command(
    user_id: str = Depends(header),
    usecase: Usecase = Depends(dependency),
) -> Token:
    return await usecase.execute(user_id=user_id)
