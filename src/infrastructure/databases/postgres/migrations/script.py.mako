"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
import typing

from alembic import op
import sqlalchemy
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: typing.Union[str, None] = ${repr(down_revision)}
branch_labels: typing.Union[str, typing.Sequence[str], None] = ${repr(branch_labels)}
depends_on: typing.Union[str, typing.Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
