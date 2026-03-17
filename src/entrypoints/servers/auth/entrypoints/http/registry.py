from src.framework.routing import APIRouter

from . import public


router = APIRouter()

router.include_router(public.router)
