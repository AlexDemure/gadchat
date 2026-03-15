from src.framework.routing import APIRouter

from . import get
from . import uploads


router = APIRouter()
router.include_router(uploads.router)
router.include_router(get.router)
