from src.framework.routing import APIRouter

from . import created
from . import pinned
from . import read
from . import unpinned


router = APIRouter()

router.include_router(created.router)
router.include_router(pinned.router)
router.include_router(unpinned.router)
router.include_router(read.router)
