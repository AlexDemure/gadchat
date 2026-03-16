from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.infrastructure.databases.orm.sqlalchemy.tables import Base
from src.infrastructure.databases.postgres.collections import LENGTH_MIDDLE_STR
from src.infrastructure.databases.postgres.collections import LENGTH_PK_STR


class Role(Base):
    __tablename__ = "role"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    name: Mapped[str] = mapped_column(String(LENGTH_MIDDLE_STR), nullable=False)
