from src.framework.routing import APIRouter

from . import created
from . import messages
from . import position


router = APIRouter()

router.include_router(created.router)
router.include_router(position.router)
router.include_router(messages.router)
