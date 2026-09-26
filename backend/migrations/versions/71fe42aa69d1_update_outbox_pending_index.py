from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "71fe42aa69d1"
down_revision = "8034efd764fb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    op.execute("DROP INDEX IF EXISTS ix_outbox_events_unprocessed_created_at")

    op.create_index(
        "ix_outbox_events_pending_created_at",
        "outbox_events",
        ["created_at"],
        unique=False,
        postgresql_where=sa.text("processed_at IS NULL AND failed_at IS NULL"),
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_outbox_events_pending_created_at")

    op.create_index(
        "ix_outbox_events_unprocessed_created_at",
        "outbox_events",
        ["created_at"],
        unique=False,
        postgresql_where=sa.text("processed_at IS NULL"),
    )
