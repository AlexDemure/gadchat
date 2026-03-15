from src.entrypoints.http.common.schemas import Health
from src.framework.routing import APIRouter


router = APIRouter()


@router.get("/health", response_model=Health)
async def query() -> dict[str, str]:
    return {"status": "ok"}
