import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.infrastructure.databases.orm.sqlalchemy.tables import Base
from src.infrastructure.databases.postgres.collections import LENGTH_MIDDLE_STR
from src.infrastructure.databases.postgres.collections import LENGTH_PK_STR
from src.infrastructure.databases.postgres.collections import LENGTH_TEXT


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)

    title: Mapped[str | None] = mapped_column(String(LENGTH_MIDDLE_STR), nullable=True)

    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    options: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)

    members: Mapped[list["Member"]] = relationship("Member", uselist=True, viewonly=True)
    messages: Mapped[list["Message"]] = relationship("Message", uselist=True, viewonly=True)


class Member(Base):
    __tablename__ = "member"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    chat_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("chat.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("role.id", ondelete="CASCADE"),
        nullable=False,
    )

    position: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notifications: Mapped[int] = mapped_column(BigInteger, nullable=False)

    chat = relationship("Chat", uselist=False, viewonly=True)
    user = relationship("User", uselist=False, viewonly=True)
    role = relationship("Role", uselist=False, viewonly=True)
    messages = relationship("Message", uselist=True, viewonly=True)


class Message(Base):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    chat_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("chat.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
    )
    member_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("member.id", ondelete="CASCADE"),
        nullable=True,
    )

    kind: Mapped[str] = mapped_column(String(LENGTH_PK_STR), nullable=False)
    text: Mapped[str | None] = mapped_column(String(LENGTH_TEXT), nullable=True)

    pinned: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    edited: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    member = relationship("Member", uselist=False, viewonly=True)
    user = relationship("User", uselist=False, viewonly=True)

    _reply = relationship(
        "Reply",
        uselist=False,
        viewonly=True,
        foreign_keys="Reply.message_id",
    )
    _forward = relationship(
        "Forward",
        uselist=False,
        viewonly=True,
        foreign_keys="Forward.message_id",
    )
    _attachments = relationship("Attachment", uselist=True, viewonly=True)
    reads = relationship("Read", uselist=True, viewonly=True)

    reply = association_proxy("_reply", "source_message")
    forward = association_proxy("_forward", "source_message")
    attachments = association_proxy("_attachments", "file")


class Attachment(Base):
    __tablename__ = "attachment"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("message.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("file.id", ondelete="CASCADE"),
        nullable=False,
    )

    message = relationship("Message", uselist=False, viewonly=True)
    file = relationship("File", uselist=False, viewonly=True)


class Reply(Base):
    __tablename__ = "reply"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("message.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_message_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("message.id", ondelete="CASCADE"),
        nullable=False,
    )

    @declared_attr
    def message(self):  # type:ignore
        return relationship("Message", foreign_keys=[self.message_id], viewonly=True, uselist=False)

    @declared_attr
    def source_message(self):  # type:ignore
        return relationship("Message", foreign_keys=[self.source_message_id], viewonly=True, uselist=False)


class Forward(Base):
    __tablename__ = "forward"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("message.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_message_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("message.id", ondelete="CASCADE"),
        nullable=False,
    )

    @declared_attr
    def message(self):  # type:ignore
        return relationship("Message", foreign_keys=[self.message_id], viewonly=True, uselist=False)

    @declared_attr
    def source_message(self):  # type:ignore
        return relationship("Message", foreign_keys=[self.source_message_id], viewonly=True, uselist=False)


class Read(Base):
    __tablename__ = "read"

    id: Mapped[str] = mapped_column(String(LENGTH_PK_STR), primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("message.id", ondelete="CASCADE"),
        nullable=False,
    )
    member_id: Mapped[str] = mapped_column(
        String(LENGTH_PK_STR),
        ForeignKey("member.id", ondelete="CASCADE"),
        nullable=False,
    )

    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    message = relationship("Message", uselist=False, viewonly=True)
    member = relationship("Member", uselist=False, viewonly=True)
