from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.postgres import tables


class Event(Base[tables.Event]):
    table = tables.Event
