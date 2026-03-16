import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.infrastructure.databases.orm.sqlalchemy.tables import Base
from src.infrastructure.databases.postgres.collections import LENGTH_LARGE_STR
from src.infrastructure.databases.postgres.collections import LENGTH_PK_STR
from src.infrastructure.databases.postgres.collections import LENGTH_SMALL_STR


class File(Base):
    __tablename__ = "file"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    storage: Mapped[str] = mapped_column(String(LENGTH_PK_STR), nullable=False)
    bucket: Mapped[str] = mapped_column(String(LENGTH_SMALL_STR), nullable=False)
    key: Mapped[str] = mapped_column(String(LENGTH_LARGE_STR), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(LENGTH_LARGE_STR), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(LENGTH_SMALL_STR), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=False)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
