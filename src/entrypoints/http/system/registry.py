from src.framework.routing import APIRouter

from . import routers


router = APIRouter()
router.include_router(routers.router)
