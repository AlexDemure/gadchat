from src.framework.routing import APIRouter

from . import users


router = APIRouter()

router.include_router(users.router, tags=["User"])
