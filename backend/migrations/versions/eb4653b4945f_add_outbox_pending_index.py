"""add outbox pending index

Revision ID: eb4653b4945f
Revises: 3a8e3c9da5f1
Create Date: 2026-09-20 15:56:36.045818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb4653b4945f'
down_revision: Union[str, Sequence[str], None] = '3a8e3c9da5f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_index(
        "ix_outbox_events_unprocessed_created_at",
        "outbox_events",
        ["created_at"],
        unique=False,
        postgresql_where=sa.text("processed_at IS NULL"),
    )


def downgrade():
    op.drop_index(
        "ix_outbox_events_unprocessed_created_at",
        table_name="outbox_events",
    )