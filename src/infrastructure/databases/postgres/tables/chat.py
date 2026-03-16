import datetime
import uuid

import sqlalchemy

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
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
    options: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Member(Base):
    __tablename__ = "member"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user: Mapped[User] = relationship(back_populates="member")
    chats: Mapped[list["ChatMember"]] = relationship(back_populates="member")
    messages: Mapped[list["Message"]] = relationship(back_populates="member")


class ChatMember(Base):
    __tablename__ = "chat_member"
    __table_args__ = (UniqueConstraint("chat_id", "member_id", name="uq_chat_member_chat_member"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    shard_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat.id", ondelete="CASCADE"), index=True, nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id", ondelete="CASCADE"), index=True, nullable=False
    )
    last_read_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    member: Mapped[Member] = relationship(back_populates="chats")
    reads: Mapped[list["MessageRead"]] = relationship(back_populates="chat_member")
    pin: Mapped["ChatPin | None"] = relationship(back_populates="chat_member", cascade="all, delete-orphan")


class ChatPin(Base):
    __tablename__ = "chat_pin"
    __table_args__ = (UniqueConstraint("chat_member_id", name="uq_chat_pin_chat_member"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    chat_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_member.id", ondelete="CASCADE"), index=True, nullable=False
    )
    position: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    chat_member: Mapped[ChatMember] = relationship(back_populates="pin")


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
    pinned_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    member: Mapped[Member] = relationship(back_populates="messages")
    attachments: Mapped[list["MessageFile"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    reads: Mapped[list["MessageRead"]] = relationship(back_populates="message", cascade="all, delete-orphan")


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


class MessageRead(Base):
    __tablename__ = "message_read"
    __table_args__ = (
        UniqueConstraint("message_id", "chat_member_id", name="uq_message_read_message_chat_member"),
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
    chat_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_member.id", ondelete="CASCADE"), index=True, nullable=False
    )
    read_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message: Mapped[Message] = relationship(back_populates="reads")
    chat_member: Mapped[ChatMember] = relationship(back_populates="reads")
