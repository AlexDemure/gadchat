import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.infrastructure.databases.orm.sqlalchemy.tables import Base
from src.infrastructure.databases.postgres.collections import LENGTH_PK_STR


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_seen_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    options: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    member: Mapped["Member | None"] = relationship(back_populates="user")
