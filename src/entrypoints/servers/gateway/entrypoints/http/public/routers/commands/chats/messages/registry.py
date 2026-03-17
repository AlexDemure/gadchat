from src.framework.routing import APIRouter

from . import create
from . import pinned
from . import read
from . import unpinned


router = APIRouter()

router.include_router(create.router)
router.include_router(pinned.router)
router.include_router(unpinned.router)
router.include_router(read.router)
