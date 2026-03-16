"""chat user refactor

Revision ID: 9f2e7b1f4c6a
Revises: 82f9d9c5fcb2
Create Date: 2026-03-16 18:20:00.000000

"""

import typing
import uuid

import sqlalchemy

from alembic import op


revision: str = "9f2e7b1f4c6a"
down_revision: typing.Union[str, None] = "82f9d9c5fcb2"
branch_labels: typing.Union[str, typing.Sequence[str], None] = None
depends_on: typing.Union[str, typing.Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "user",
        sqlalchemy.Column("id", sqlalchemy.String(length=256), nullable=False),
        sqlalchemy.Column("online", sqlalchemy.Boolean(), nullable=False),
        sqlalchemy.Column("last_seen_at", sqlalchemy.DateTime(timezone=True), nullable=True),
        sqlalchemy.PrimaryKeyConstraint("id", name="pk_user"),
    )

    bind.execute(
        sqlalchemy.text(
            """
            INSERT INTO "user" (id, online, last_seen_at)
            SELECT DISTINCT member.user_id, FALSE, NULL
            FROM member
            """
        )
    )
    bind.execute(
        sqlalchemy.text(
            """
            INSERT INTO "user" (id, online, last_seen_at)
            SELECT presence.user_id, presence.online, presence.last_seen_at
            FROM presence
            ON CONFLICT (id)
            DO UPDATE SET
                online = EXCLUDED.online,
                last_seen_at = EXCLUDED.last_seen_at
            """
        )
    )

    op.rename_table("member", "chat_member")
    op.drop_index("ix_member_user_id", table_name="chat_member")
    op.drop_index("ix_member_chat_id", table_name="chat_member")
    op.drop_index("ix_member_shard_id", table_name="chat_member")
    op.drop_index("ix_member_pin_position", table_name="chat_member")
    op.drop_constraint("uq_member_chat_user", "chat_member", type_="unique")

    op.alter_column("chat_member", "pin_position", new_column_name="position")
    op.add_column("chat_member", sqlalchemy.Column("member_id", sqlalchemy.UUID(), nullable=True))
    op.add_column("chat_member", sqlalchemy.Column("last_read_at", sqlalchemy.DateTime(timezone=True), nullable=True))

    op.create_table(
        "member",
        sqlalchemy.Column("id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("user_id", sqlalchemy.String(length=256), nullable=False),
        sqlalchemy.Column("created", sqlalchemy.DateTime(timezone=True), nullable=False),
        sqlalchemy.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_member_user_id_user", ondelete="CASCADE"),
        sqlalchemy.PrimaryKeyConstraint("id", name="pk_member_profile"),
        sqlalchemy.UniqueConstraint("user_id", name="uq_member_user_id"),
    )
    op.create_index(op.f("ix_member_user_id"), "member", ["user_id"], unique=False)

    rows = bind.execute(sqlalchemy.text("SELECT DISTINCT user_id, MIN(created) AS created FROM chat_member GROUP BY user_id"))
    member_ids: dict[str, uuid.UUID] = {}
    for user_id, created in rows:
        member_id = uuid.uuid4()
        member_ids[user_id] = member_id
        bind.execute(
            sqlalchemy.text(
                """
                INSERT INTO member (id, user_id, created)
                VALUES (:id, :user_id, :created)
                """
            ),
            {
                "id": member_id,
                "user_id": user_id,
                "created": created,
            },
        )

    for user_id, member_id in member_ids.items():
        bind.execute(
            sqlalchemy.text(
                """
                UPDATE chat_member
                SET member_id = :member_id
                WHERE user_id = :user_id
                """
            ),
            {
                "member_id": member_id,
                "user_id": user_id,
            },
        )

    bind.execute(
        sqlalchemy.text(
            """
            UPDATE message
            SET member_id = chat_member.member_id
            FROM chat_member
            WHERE message.member_id = chat_member.id
            """
        )
    )

    op.drop_constraint("fk_message_member_id_member", "message", type_="foreignkey")
    op.create_foreign_key(
        "fk_message_member_id_member_profile",
        "message",
        "member",
        ["member_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.alter_column("chat_member", "member_id", nullable=False)
    op.drop_column("chat_member", "user_id")

    op.create_index(op.f("ix_chat_member_chat_id"), "chat_member", ["chat_id"], unique=False)
    op.create_index(op.f("ix_chat_member_member_id"), "chat_member", ["member_id"], unique=False)
    op.create_index(op.f("ix_chat_member_position"), "chat_member", ["position"], unique=False)
    op.create_index(op.f("ix_chat_member_shard_id"), "chat_member", ["shard_id"], unique=False)
    op.create_unique_constraint("uq_chat_member_chat_member", "chat_member", ["chat_id", "member_id"])

    op.create_table(
        "message_read",
        sqlalchemy.Column("id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("shard_id", sqlalchemy.BigInteger(), nullable=False),
        sqlalchemy.Column("chat_id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("message_id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("chat_member_id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("read_at", sqlalchemy.DateTime(timezone=True), nullable=False),
        sqlalchemy.ForeignKeyConstraint(
            ["chat_member_id"],
            ["chat_member.id"],
            name="fk_message_read_chat_member_id_chat_member",
            ondelete="CASCADE",
        ),
        sqlalchemy.ForeignKeyConstraint(
            ["message_id", "chat_id"],
            ["message.id", "message.chat_id"],
            name="fk_message_read_message_id_chat_id_message",
            ondelete="CASCADE",
        ),
        sqlalchemy.PrimaryKeyConstraint("id", name="pk_message_read"),
        sqlalchemy.UniqueConstraint("message_id", "chat_member_id", name="uq_message_read_message_chat_member"),
    )
    op.create_index(op.f("ix_message_read_chat_id"), "message_read", ["chat_id"], unique=False)
    op.create_index(op.f("ix_message_read_chat_member_id"), "message_read", ["chat_member_id"], unique=False)
    op.create_index(op.f("ix_message_read_message_id"), "message_read", ["message_id"], unique=False)
    op.create_index(op.f("ix_message_read_shard_id"), "message_read", ["shard_id"], unique=False)

    op.drop_table("presence")


def downgrade() -> None:
    op.create_table(
        "presence",
        sqlalchemy.Column("user_id", sqlalchemy.String(length=256), nullable=False),
        sqlalchemy.Column("online", sqlalchemy.Boolean(), nullable=False),
        sqlalchemy.Column("last_seen_at", sqlalchemy.DateTime(timezone=True), nullable=True),
        sqlalchemy.PrimaryKeyConstraint("user_id", name="pk_presence"),
    )
    op.execute(
        """
        INSERT INTO presence (user_id, online, last_seen_at)
        SELECT id, online, last_seen_at
        FROM "user"
        """
    )

    op.drop_index(op.f("ix_message_read_shard_id"), table_name="message_read")
    op.drop_index(op.f("ix_message_read_message_id"), table_name="message_read")
    op.drop_index(op.f("ix_message_read_chat_member_id"), table_name="message_read")
    op.drop_index(op.f("ix_message_read_chat_id"), table_name="message_read")
    op.drop_table("message_read")

    op.drop_constraint("fk_message_member_id_member_profile", "message", type_="foreignkey")
    op.create_foreign_key(
        "fk_message_member_id_member",
        "message",
        "chat_member",
        ["member_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.add_column("chat_member", sqlalchemy.Column("user_id", sqlalchemy.String(length=256), nullable=True))
    op.execute(
        """
        UPDATE chat_member
        SET user_id = member.user_id
        FROM member
        WHERE chat_member.member_id = member.id
        """
    )
    op.alter_column("chat_member", "user_id", nullable=False)

    op.execute(
        """
        UPDATE message
        SET member_id = chat_member.id
        FROM chat_member
        JOIN member ON member.id = chat_member.member_id
        WHERE message.member_id = member.id
        """
    )

    op.drop_constraint("uq_chat_member_chat_member", "chat_member", type_="unique")
    op.drop_index(op.f("ix_chat_member_shard_id"), table_name="chat_member")
    op.drop_index(op.f("ix_chat_member_position"), table_name="chat_member")
    op.drop_index(op.f("ix_chat_member_member_id"), table_name="chat_member")
    op.drop_index(op.f("ix_chat_member_chat_id"), table_name="chat_member")
    op.drop_column("chat_member", "last_read_at")
    op.drop_column("chat_member", "member_id")
    op.alter_column("chat_member", "position", new_column_name="pin_position")

    op.drop_index(op.f("ix_member_user_id"), table_name="member")
    op.drop_table("member")

    op.create_unique_constraint("uq_member_chat_user", "chat_member", ["chat_id", "user_id"])
    op.create_index(op.f("ix_member_chat_id"), "chat_member", ["chat_id"], unique=False)
    op.create_index(op.f("ix_member_pin_position"), "chat_member", ["pin_position"], unique=False)
    op.create_index(op.f("ix_member_shard_id"), "chat_member", ["shard_id"], unique=False)
    op.create_index(op.f("ix_member_user_id"), "chat_member", ["user_id"], unique=False)
    op.rename_table("chat_member", "member")

    op.drop_table("user")
