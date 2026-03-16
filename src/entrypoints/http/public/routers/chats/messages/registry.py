from src.framework.routing import APIRouter

from . import create
from . import pin
from . import read
from . import search
from . import unpin


router = APIRouter()
router.include_router(create.router)
router.include_router(pin.router)
router.include_router(read.router)
router.include_router(search.router)
router.include_router(unpin.router)
