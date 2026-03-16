from fastapi import HTTPException
from fastapi import UploadFile

from src.common.files.collections import Mimetype


def checktype(*, file: UploadFile, allowed: set[Mimetype], error_detail: str) -> None:
    if not file.content_type:
        raise HTTPException(status_code=400, detail=error_detail)

    try:
        mimetype = Mimetype(file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=error_detail) from exc

    if mimetype not in allowed:
        raise HTTPException(status_code=415, detail=error_detail)
