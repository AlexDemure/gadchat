from src.framework.routing import APIRouter

from . import demo
from . import list
from . import messages
from . import ws


router = APIRouter()
router.include_router(demo.router)
router.include_router(ws.router)
router.include_router(messages.router)
router.include_router(list.router)
