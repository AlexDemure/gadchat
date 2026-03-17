from src.entrypoints.servers.observer.entrypoints.http import demo
from src.framework.routing import APIRouter


router = APIRouter()

router.include_router(demo.router)
