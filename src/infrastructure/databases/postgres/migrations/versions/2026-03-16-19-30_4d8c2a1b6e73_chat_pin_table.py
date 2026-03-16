"""chat pin table

Revision ID: 4d8c2a1b6e73
Revises: b7c1d2e4a991
Create Date: 2026-03-16 19:30:00.000000

"""

import typing
import uuid

import sqlalchemy

from alembic import op


revision: str = "4d8c2a1b6e73"
down_revision: typing.Union[str, None] = "b7c1d2e4a991"
branch_labels: typing.Union[str, typing.Sequence[str], None] = None
depends_on: typing.Union[str, typing.Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "chat_pin",
        sqlalchemy.Column("id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("chat_member_id", sqlalchemy.UUID(), nullable=False),
        sqlalchemy.Column("position", sqlalchemy.BigInteger(), nullable=False),
        sqlalchemy.Column("created", sqlalchemy.DateTime(timezone=True), nullable=False),
        sqlalchemy.ForeignKeyConstraint(
            ["chat_member_id"],
            ["chat_member.id"],
            name="fk_chat_pin_chat_member_id_chat_member",
            ondelete="CASCADE",
        ),
        sqlalchemy.PrimaryKeyConstraint("id", name="pk_chat_pin"),
        sqlalchemy.UniqueConstraint("chat_member_id", name="uq_chat_pin_chat_member"),
    )
    op.create_index(op.f("ix_chat_pin_chat_member_id"), "chat_pin", ["chat_member_id"], unique=False)
    op.create_index(op.f("ix_chat_pin_position"), "chat_pin", ["position"], unique=False)

    rows = bind.execute(
        sqlalchemy.text(
            """
            SELECT id, position, created
            FROM chat_member
            WHERE position IS NOT NULL
            ORDER BY position ASC, id ASC
            """
        )
    )
    for chat_member_id, position, created in rows:
        bind.execute(
            sqlalchemy.text(
                """
                INSERT INTO chat_pin (id, chat_member_id, position, created)
                VALUES (:id, :chat_member_id, :position, :created)
                """
            ),
            {
                "id": uuid.uuid4(),
                "chat_member_id": chat_member_id,
                "position": position,
                "created": created,
            },
        )

    op.drop_index(op.f("ix_chat_member_position"), table_name="chat_member")
    op.drop_column("chat_member", "position")


def downgrade() -> None:
    op.add_column("chat_member", sqlalchemy.Column("position", sqlalchemy.BigInteger(), nullable=True))
    op.create_index(op.f("ix_chat_member_position"), "chat_member", ["position"], unique=False)
    op.execute(
        """
        UPDATE chat_member
        SET position = chat_pin.position
        FROM chat_pin
        WHERE chat_pin.chat_member_id = chat_member.id
        """
    )
    op.drop_index(op.f("ix_chat_pin_position"), table_name="chat_pin")
    op.drop_index(op.f("ix_chat_pin_chat_member_id"), table_name="chat_pin")
    op.drop_table("chat_pin")
