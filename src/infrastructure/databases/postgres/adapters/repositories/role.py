from src.domain.collections import exceptions
from src.infrastructure.databases.postgres import crud
from src.infrastructure.databases.postgres import tables

from .base import Base


class Role(Base[crud.Role, tables.Role, exceptions.RoleNotFound]):
    crud = crud.Role
    table = tables.Role
    error = exceptions.RoleNotFound
