from src.framework.routing import APIRouter

from . import demo


router = APIRouter()

router.include_router(demo.router)
