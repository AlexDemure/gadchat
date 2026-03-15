from src.framework.routing import APIRouter

from . import chats
from . import users


router = APIRouter()
router.include_router(users.router)
router.include_router(chats.router)
