from src.framework.routing import APIRouter

from . import websocket


router = APIRouter()
router.include_router(websocket.router)
