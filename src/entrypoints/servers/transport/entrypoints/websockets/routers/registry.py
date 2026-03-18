from src.framework.routing import APIRouter

from . import session


router = APIRouter()

router.include_router(session.router)
