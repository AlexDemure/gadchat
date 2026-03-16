from src.application.collections import exceptions
from src.infrastructure.databases.postgres import crud
from src.infrastructure.databases.postgres import tables

from .base import Base


class User(Base[crud.User, tables.User, exceptions.UserNotFound]):
    crud = crud.User
    table = tables.User
    error = exceptions.UserNotFound

    async def ensure(self, external_id: str) -> tables.User:
        return await self.crud.ensure(self.session, external_id=external_id)
