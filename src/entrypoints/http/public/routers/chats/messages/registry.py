from src.framework.routing import APIRouter

from . import create
from . import list


router = APIRouter()
router.include_router(create.router)
router.include_router(list.router)
