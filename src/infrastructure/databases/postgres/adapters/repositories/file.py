from src.application.collections import exceptions
from src.infrastructure.databases.postgres import crud
from src.infrastructure.databases.postgres import tables

from .base import Base


class File(Base[crud.File, tables.File, exceptions.FileNotFound]):
    crud = crud.File
    table = tables.File
    error = exceptions.FileNotFound
