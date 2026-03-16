from src.framework.routing import APIRouter

from . import create
from . import files
from . import messages
from . import position
from . import search


router = APIRouter()


router.include_router(create.router)
router.include_router(search.router)
router.include_router(position.router)
router.include_router(files.router)
router.include_router(messages.router)
