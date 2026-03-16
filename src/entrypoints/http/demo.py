from fastapi import status
from fastapi.responses import FileResponse

from src.framework.routing import APIRouter


router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, description="Serve chat demo page")
async def query() -> FileResponse:
    return FileResponse("src/static/html/chats-demo.html", media_type="text/html")
