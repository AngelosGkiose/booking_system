"""add user role

Revision ID: a6ec8fa9d1c6
Revises: 71fe42aa69d1
Create Date: 2026-09-23 20:54:33.026374
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6ec8fa9d1c6"
down_revision: Union[str, Sequence[str], None] = "71fe42aa69d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role_enum = sa.Enum(
        "ADMIN",
        "USER",
        name="user_role"
    )

    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            server_default="USER",
            nullable=False
        )
    )


def downgrade() -> None:
    op.drop_column("users", "role")

    user_role_enum = sa.Enum(
        "ADMIN",
        "USER",
        name="user_role"
    )

    user_role_enum.drop(op.get_bind(), checkfirst=True)