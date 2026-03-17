"""events

Revision ID: a6eec7f4c9c1
Revises: 3008266d3412
Create Date: 2026-03-17 12:00:00.000000

"""

import typing

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a6eec7f4c9c1"
down_revision: typing.Union[str, None] = "3008266d3412"
branch_labels: typing.Union[str, typing.Sequence[str], None] = None
depends_on: typing.Union[str, typing.Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event",
        sa.Column("id", sa.String(length=256), nullable=False),
        sa.Column("type", sa.String(length=256), nullable=False),
        sa.Column("name", sa.String(length=2048), nullable=False),
        sa.Column("priority", sa.BigInteger(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dispatched", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(length=16384), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_dispatch", "event", ["type", "dispatched", "failed", "priority", "created"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_event_dispatch", table_name="event")
    op.drop_table("event")
