from src.framework.routing import APIRouter

from . import login
from . import current


router = APIRouter()

router.include_router(login.router)
router.include_router(current.router)
