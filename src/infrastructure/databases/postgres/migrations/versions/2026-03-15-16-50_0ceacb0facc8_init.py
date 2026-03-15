"""init

Revision ID: 0ceacb0facc8
Revises:
Create Date: 2026-03-15 16:50:00.000000

"""

import typing

import sqlalchemy

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0ceacb0facc8"
down_revision: typing.Union[str, None] = None
branch_labels: typing.Union[str, typing.Sequence[str], None] = None
depends_on: typing.Union[str, typing.Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat",
        sqlalchemy.Column("id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("shard_id", sqlalchemy.BigInteger(), nullable=False),
        sqlalchemy.Column("kind", sqlalchemy.String(length=256), nullable=False),
        sqlalchemy.Column("title", sqlalchemy.String(length=8192), nullable=True),
        sqlalchemy.Column("created", sqlalchemy.DateTime(timezone=True), nullable=False),
        sqlalchemy.PrimaryKeyConstraint("id", name="pk_chat"),
    )
    op.create_index(op.f("ix_chat_shard_id"), "chat", ["shard_id"], unique=False)

    op.create_table(
        "file",
        sqlalchemy.Column("id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("storage", sqlalchemy.String(length=256), nullable=False),
        sqlalchemy.Column("bucket", sqlalchemy.String(length=1024), nullable=False),
        sqlalchemy.Column("key", sqlalchemy.String(length=8192), nullable=False),
        sqlalchemy.Column("filename", sqlalchemy.String(length=8192), nullable=True),
        sqlalchemy.Column("content_type", sqlalchemy.String(length=1024), nullable=True),
        sqlalchemy.Column("size_bytes", sqlalchemy.BigInteger(), nullable=True),
        sqlalchemy.Column("created", sqlalchemy.DateTime(timezone=True), nullable=False),
        sqlalchemy.PrimaryKeyConstraint("id", name="pk_file"),
        sqlalchemy.UniqueConstraint("bucket", "key", name="uq_files_bucket_key"),
    )
    op.create_index(op.f("ix_file_bucket"), "file", ["bucket"], unique=False)
    op.create_index(op.f("ix_file_key"), "file", ["key"], unique=False)

    op.create_table(
        "member",
        sqlalchemy.Column("id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("shard_id", sqlalchemy.BigInteger(), nullable=False),
        sqlalchemy.Column("chat_id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("user_id", sqlalchemy.String(length=256), nullable=False),
        sqlalchemy.Column("created", sqlalchemy.DateTime(timezone=True), nullable=False),
        sqlalchemy.ForeignKeyConstraint(["chat_id"], ["chat.id"], name="fk_member_chat_id_chat", ondelete="CASCADE"),
        sqlalchemy.PrimaryKeyConstraint("id", name="pk_member"),
        sqlalchemy.UniqueConstraint("chat_id", "user_id", name="uq_member_chat_user"),
    )
    op.create_index(op.f("ix_member_chat_id"), "member", ["chat_id"], unique=False)
    op.create_index(op.f("ix_member_shard_id"), "member", ["shard_id"], unique=False)
    op.create_index(op.f("ix_member_user_id"), "member", ["user_id"], unique=False)

    op.execute(
        """
        CREATE TABLE message (
            id UUID NOT NULL,
            shard_id BIGINT NOT NULL,
            chat_id UUID NOT NULL,
            member_id UUID NOT NULL,
            body VARCHAR(16384),
            created TIMESTAMP WITH TIME ZONE,
            CONSTRAINT pk_message PRIMARY KEY (id, chat_id),
            CONSTRAINT fk_message_chat_id_chat FOREIGN KEY (chat_id) REFERENCES chat(id) ON DELETE CASCADE,
            CONSTRAINT fk_message_member_id_member FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE CASCADE
        ) PARTITION BY HASH (chat_id)
        """
    )
    for remainder in range(16):
        op.execute(
            f"""
            CREATE TABLE message_p{remainder}
            PARTITION OF message
            FOR VALUES WITH (MODULUS 16, REMAINDER {remainder})
            """
        )
    op.create_index(op.f("ix_message_chat_id"), "message", ["chat_id"], unique=False)
    op.create_index(op.f("ix_message_member_id"), "message", ["member_id"], unique=False)
    op.create_index(op.f("ix_message_shard_id"), "message", ["shard_id"], unique=False)

    op.create_table(
        "message_file",
        sqlalchemy.Column("id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("shard_id", sqlalchemy.BigInteger(), nullable=False),
        sqlalchemy.Column("chat_id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("message_id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("file_id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("position", sqlalchemy.BigInteger(), nullable=False),
        sqlalchemy.Column("created", sqlalchemy.DateTime(timezone=True), nullable=False),
        sqlalchemy.ForeignKeyConstraint(
            ["file_id"], ["file.id"], name="fk_message_file_file_id_file", ondelete="CASCADE"
        ),
        sqlalchemy.ForeignKeyConstraint(
            ["message_id", "chat_id"],
            ["message.id", "message.chat_id"],
            name="fk_message_file_message_id_chat_id_message",
            ondelete="CASCADE",
        ),
        sqlalchemy.PrimaryKeyConstraint("id", name="pk_message_file"),
    )
    op.create_index(op.f("ix_message_file_chat_id"), "message_file", ["chat_id"], unique=False)
    op.create_index(op.f("ix_message_file_file_id"), "message_file", ["file_id"], unique=False)
    op.create_index(op.f("ix_message_file_message_id"), "message_file", ["message_id"], unique=False)
    op.create_index(op.f("ix_message_file_shard_id"), "message_file", ["shard_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_message_file_shard_id"), table_name="message_file")
    op.drop_index(op.f("ix_message_file_chat_id"), table_name="message_file")
    op.drop_index(op.f("ix_message_file_message_id"), table_name="message_file")
    op.drop_index(op.f("ix_message_file_file_id"), table_name="message_file")
    op.drop_table("message_file")

    op.drop_index(op.f("ix_message_shard_id"), table_name="message")
    op.drop_index(op.f("ix_message_member_id"), table_name="message")
    op.drop_index(op.f("ix_message_chat_id"), table_name="message")
    for remainder in range(16):
        op.execute(f"DROP TABLE IF EXISTS message_p{remainder}")
    op.drop_table("message")

    op.drop_index(op.f("ix_member_user_id"), table_name="member")
    op.drop_index(op.f("ix_member_shard_id"), table_name="member")
    op.drop_index(op.f("ix_member_chat_id"), table_name="member")
    op.drop_table("member")

    op.drop_index(op.f("ix_file_key"), table_name="file")
    op.drop_index(op.f("ix_file_bucket"), table_name="file")
    op.drop_table("file")

    op.drop_index(op.f("ix_chat_shard_id"), table_name="chat")
    op.drop_table("chat")
