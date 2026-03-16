from fastapi import Header


async def header(x_user_id: str = Header(alias="x-user-id")) -> str:
    return x_user_id
