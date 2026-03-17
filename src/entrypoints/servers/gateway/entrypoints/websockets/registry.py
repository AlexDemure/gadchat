from src.framework.routing import APIRouter

from . import connect


router = APIRouter()
router.include_router(connect.router)
