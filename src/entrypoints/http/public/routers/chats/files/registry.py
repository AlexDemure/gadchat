from src.framework.routing import APIRouter

from . import uploads

router = APIRouter()

router.include_router(uploads.router)
