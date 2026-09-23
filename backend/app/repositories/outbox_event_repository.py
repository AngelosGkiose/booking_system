from datetime import datetime, timezone

from app.models import OutboxEventModel
from sqlalchemy import or_

def create_outbox_event_repo(outbox_event,db):
    db.add(outbox_event)
    db.flush()
    return outbox_event


def get_unprocessed_outbox_events_repo(db,limit=100):
    return db.query(OutboxEventModel).filter(OutboxEventModel.processed_at.is_(None),OutboxEventModel.failed_at.is_(None)).order_by(OutboxEventModel.created_at).limit(limit).with_for_update(skip_locked=True).all()


def get_unprocessed_outbox_event_ids_repo(db, limit=100):
    now = datetime.now(timezone.utc)

    rows = (
        db.query(OutboxEventModel.id)
        .filter(
            OutboxEventModel.processed_at.is_(None),
            OutboxEventModel.failed_at.is_(None),
            or_(
                OutboxEventModel.next_attempt_at.is_(None),
                OutboxEventModel.next_attempt_at <= now
            )
        )
        .order_by(OutboxEventModel.created_at)
        .limit(limit)
        .all()
    )

    return [row[0] for row in rows]
def get_outbox_event_for_update_repo(event_id, db):
    now = datetime.now(timezone.utc)

    return (
        db.query(OutboxEventModel)
        .filter(
            OutboxEventModel.id == event_id,
            OutboxEventModel.processed_at.is_(None),
            OutboxEventModel.failed_at.is_(None),
            or_(
                OutboxEventModel.next_attempt_at.is_(None),
                OutboxEventModel.next_attempt_at <= now
            )
        )
        .with_for_update(skip_locked=True)
        .first()
    )


def get_failed_outbox_events_count_repo(db):
    return db.query(OutboxEventModel).filter(OutboxEventModel.failed_at.is_not(None)).count()