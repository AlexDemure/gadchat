from fastapi import Header
from fastapi import HTTPException


async def header(x_user_id: str = Header(alias='x-user-id')) -> str:
    return x_user_id
