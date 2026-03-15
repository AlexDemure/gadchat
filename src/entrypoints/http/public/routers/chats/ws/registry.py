from src.framework.routing import APIRouter

from . import ticket


router = APIRouter()
router.include_router(ticket.router)
