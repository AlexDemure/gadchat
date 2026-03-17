from src.framework.routing import APIRouter

from . import chats


router = APIRouter()
router.include_router(chats.router)
