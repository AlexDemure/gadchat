"""chat user options

Revision ID: b7c1d2e4a991
Revises: 9f2e7b1f4c6a
Create Date: 2026-03-16 18:45:00.000000

"""

import typing

import sqlalchemy

from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "b7c1d2e4a991"
down_revision: typing.Union[str, None] = "9f2e7b1f4c6a"
branch_labels: typing.Union[str, typing.Sequence[str], None] = None
depends_on: typing.Union[str, typing.Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat",
        sqlalchemy.Column(
            "options",
            postgresql.JSONB(astext_type=sqlalchemy.Text()),
            nullable=False,
            server_default=sqlalchemy.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "user",
        sqlalchemy.Column(
            "options",
            postgresql.JSONB(astext_type=sqlalchemy.Text()),
            nullable=False,
            server_default=sqlalchemy.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("chat", "options", server_default=None)
    op.alter_column("user", "options", server_default=None)


def downgrade() -> None:
    op.drop_column("user", "options")
    op.drop_column("chat", "options")
