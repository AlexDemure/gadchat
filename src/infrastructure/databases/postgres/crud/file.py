from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.postgres import tables


class File(Base[tables.File]):
    table = tables.File
