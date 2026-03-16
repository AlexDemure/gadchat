"""message pinned at

Revision ID: 6c4d2110a2a4
Revises: 6a4d1e4a63b1
Create Date: 2026-03-16 16:10:00.000000

"""

import typing

import sqlalchemy

from alembic import op


revision: str = "6c4d2110a2a4"
down_revision: typing.Union[str, None] = "6a4d1e4a63b1"
branch_labels: typing.Union[str, typing.Sequence[str], None] = None
depends_on: typing.Union[str, typing.Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("message", sqlalchemy.Column("pinned_at", sqlalchemy.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_message_pinned_at"), "message", ["pinned_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_message_pinned_at"), table_name="message")
    op.drop_column("message", "pinned_at")
