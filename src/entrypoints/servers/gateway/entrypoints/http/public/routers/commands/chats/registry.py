from src.framework.routing import APIRouter

from . import create
from . import messages
from . import position


router = APIRouter()

router.include_router(create.router)
router.include_router(position.router)
router.include_router(messages.router)
