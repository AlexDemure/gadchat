from src.framework.routing import APIRouter

from . import commands
from . import events


router = APIRouter()

router.include_router(commands.router)
router.include_router(events.router)
