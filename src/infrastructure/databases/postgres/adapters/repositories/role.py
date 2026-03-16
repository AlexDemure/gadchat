from src.application.collections import exceptions
from src.infrastructure.databases.postgres import crud
from src.infrastructure.databases.postgres import tables

from .base import Base


class Role(Base[crud.Role, tables.Role, exceptions.RoleNotFound]):
    crud = crud.Role
    table = tables.Role
    error = exceptions.RoleNotFound

    async def ensure(self, name: str) -> tables.Role:
        return await self.crud.ensure(self.session, name=name)
