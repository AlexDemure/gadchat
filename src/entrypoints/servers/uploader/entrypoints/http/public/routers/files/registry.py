from src.framework.routing import APIRouter

from . import audio
from . import document
from . import image
from . import video


router = APIRouter()

router.include_router(image.router)
router.include_router(video.router)
router.include_router(audio.router)
router.include_router(document.router)
