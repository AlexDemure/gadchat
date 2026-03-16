"""presence

Revision ID: 82f9d9c5fcb2
Revises: 6c4d2110a2a4
Create Date: 2026-03-16 16:40:00.000000

"""

import typing

import sqlalchemy

from alembic import op


revision: str = "82f9d9c5fcb2"
down_revision: typing.Union[str, None] = "6c4d2110a2a4"
branch_labels: typing.Union[str, typing.Sequence[str], None] = None
depends_on: typing.Union[str, typing.Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "presence",
        sqlalchemy.Column("user_id", sqlalchemy.String(length=256), nullable=False),
        sqlalchemy.Column("online", sqlalchemy.Boolean(), nullable=False),
        sqlalchemy.Column("last_seen_at", sqlalchemy.DateTime(timezone=True), nullable=True),
        sqlalchemy.PrimaryKeyConstraint("user_id", name="pk_presence"),
    )


def downgrade() -> None:
    op.drop_table("presence")
