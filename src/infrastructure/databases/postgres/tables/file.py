import datetime
import uuid

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.infrastructure.databases.orm.sqlalchemy.tables import Base
from src.infrastructure.databases.postgres.collections import LENGTH_LARGE_STR
from src.infrastructure.databases.postgres.collections import LENGTH_PK_STR
from src.infrastructure.databases.postgres.collections import LENGTH_SMALL_STR


class File(Base):
    __tablename__ = "file"
    __table_args__ = (UniqueConstraint("bucket", "key", name="uq_files_bucket_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    storage: Mapped[str] = mapped_column(String(LENGTH_PK_STR))
    bucket: Mapped[str] = mapped_column(String(LENGTH_SMALL_STR), index=True)
    key: Mapped[str] = mapped_column(String(LENGTH_LARGE_STR), index=True)
    filename: Mapped[str | None] = mapped_column(String(LENGTH_LARGE_STR), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(LENGTH_SMALL_STR), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list["MessageFile"]] = relationship(back_populates="file")
