from src.framework.routing import APIRouter

from . import create
from . import files
from . import messages
from . import pin
from . import reorder
from . import search
from . import unpin


router = APIRouter()


router.include_router(create.router)
router.include_router(search.router)
router.include_router(pin.router)
router.include_router(unpin.router)
router.include_router(reorder.router)
router.include_router(files.router)
router.include_router(messages.router)
