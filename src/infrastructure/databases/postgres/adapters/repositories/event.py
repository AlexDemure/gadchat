from src.application.collections import exceptions
from src.infrastructure.databases.postgres import crud
from src.infrastructure.databases.postgres import tables

from .base import Base


class Event(Base[crud.Event, tables.Event, exceptions.EventNotFound]):
    crud = crud.Event
    table = tables.Event
    error = exceptions.EventNotFound
