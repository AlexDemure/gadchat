from src.framework.routing import APIRouter

from . import demo
from . import public


router = APIRouter()

router.include_router(public.router)
router.include_router(demo.router)
