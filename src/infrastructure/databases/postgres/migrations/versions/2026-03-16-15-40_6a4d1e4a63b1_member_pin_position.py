"""member pin position

Revision ID: 6a4d1e4a63b1
Revises: 0ceacb0facc8
Create Date: 2026-03-16 15:40:00.000000

"""

import typing

import sqlalchemy

from alembic import op


revision: str = "6a4d1e4a63b1"
down_revision: typing.Union[str, None] = "0ceacb0facc8"
branch_labels: typing.Union[str, typing.Sequence[str], None] = None
depends_on: typing.Union[str, typing.Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("member", sqlalchemy.Column("pin_position", sqlalchemy.BigInteger(), nullable=True))
    op.create_index(op.f("ix_member_pin_position"), "member", ["pin_position"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_member_pin_position"), table_name="member")
    op.drop_column("member", "pin_position")
