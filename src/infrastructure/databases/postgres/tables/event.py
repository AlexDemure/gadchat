import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.infrastructure.databases.orm.sqlalchemy.tables import Base
from src.infrastructure.databases.postgres.collections import LENGTH_MIDDLE_STR
from src.infrastructure.databases.postgres.collections import LENGTH_PK_STR
from src.infrastructure.databases.postgres.collections import LENGTH_TEXT


class Event(Base):
    __tablename__ = "event"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    type: Mapped[str] = mapped_column(String(LENGTH_PK_STR), nullable=False)
    name: Mapped[str] = mapped_column(String(LENGTH_MIDDLE_STR), nullable=False)
    priority: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dispatched: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(String(LENGTH_TEXT), nullable=True)
