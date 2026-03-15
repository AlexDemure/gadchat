from src.framework.routing import APIRouter

from . import demo
from . import public
from . import system


router = APIRouter()

router.include_router(demo.router)
router.include_router(public.router, prefix="/api")
router.include_router(system.router, prefix="/api/-")
