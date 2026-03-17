from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.postgres import tables


class Role(Base[tables.Role]):
    table = tables.Role
