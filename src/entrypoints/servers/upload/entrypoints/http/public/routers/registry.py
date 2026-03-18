from src.framework.routing import APIRouter

from . import files


router = APIRouter()

router.include_router(files.router, tags=["File"])
