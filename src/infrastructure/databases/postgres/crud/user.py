import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.databases.orm.sqlalchemy.crud import Base
from src.infrastructure.databases.postgres import tables


class User(Base[tables.User]):
    table = tables.User
