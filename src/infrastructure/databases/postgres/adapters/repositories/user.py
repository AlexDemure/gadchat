import datetime

from src.infrastructure.databases.postgres import crud
from src.infrastructure.databases.postgres import tables

from .base import Base


class User(Base[crud.User, tables.User, Exception]):
    crud = crud.User
    table = tables.User
    error = Exception

    async def update_status(
        self,
        user_id: str,
        online: bool,
        last_seen_at: datetime.datetime | None,
    ) -> tables.User:
        return await self.crud.update_status(
            self.session,
            user_id=user_id,
            online=online,
            last_seen_at=last_seen_at,
        )
