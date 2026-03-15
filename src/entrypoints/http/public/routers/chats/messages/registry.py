from src.framework.routing import APIRouter

from . import create
from . import search


router = APIRouter()
router.include_router(create.router)
router.include_router(search.router)
