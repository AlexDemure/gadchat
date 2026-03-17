from src.framework.routing import APIRouter

from . import messages
from . import search


router = APIRouter()


router.include_router(search.router)
router.include_router(messages.router, tags=["Message"])
