import datetime
import uuid

import sqlalchemy

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.infrastructure.databases.orm.sqlalchemy.tables import Base
from src.infrastructure.databases.postgres.collections import LENGTH_LARGE_STR
from src.infrastructure.databases.postgres.collections import LENGTH_PK_STR
from src.infrastructure.databases.postgres.collections import LENGTH_TEXT


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    shard_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(LENGTH_PK_STR), nullable=False)
    title: Mapped[str | None] = mapped_column(String(LENGTH_LARGE_STR), nullable=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Member(Base):
    __tablename__ = "member"
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_member_chat_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    shard_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), index=True, nullable=False)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    messages: Mapped[list["Message"]] = relationship(back_populates="member")


class Message(Base):
    __tablename__ = "message"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    shard_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat.id", ondelete="CASCADE"), primary_key=True, index=True, nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id", ondelete="CASCADE"), index=True, nullable=False
    )
    body: Mapped[str | None] = mapped_column(String(LENGTH_TEXT), nullable=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    member: Mapped[Member] = relationship(back_populates="messages")
    attachments: Mapped[list["MessageFile"]] = relationship(back_populates="message", cascade="all, delete-orphan")


class MessageFile(Base):
    __tablename__ = "message_file"
    __table_args__ = (
        sqlalchemy.ForeignKeyConstraint(
            ["message_id", "chat_id"],
            ["message.id", "message.chat_id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    shard_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("file.id", ondelete="CASCADE"), index=True, nullable=False
    )
    position: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message: Mapped[Message] = relationship(back_populates="attachments")
    file: Mapped["File"] = relationship(back_populates="messages")
