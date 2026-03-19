from src.framework.routing import APIRouter

from . import current
from . import login


router = APIRouter()

router.include_router(login.router)
router.include_router(current.router)
