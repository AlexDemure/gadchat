from src.framework.routing import APIRouter

from . import auth
from . import current


router = APIRouter()


router.include_router(auth.router)
router.include_router(current.router)
