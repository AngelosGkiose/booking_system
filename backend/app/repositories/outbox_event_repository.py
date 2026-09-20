from app.models import OutboxEventModel


def create_outbox_event_repo(outbox_event,db):
    db.add(outbox_event)
    db.flush()
    return outbox_event


def get_unprocessed_outbox_events_repo(db):
    return db.query(OutboxEventModel).filter(OutboxEventModel.processed_at.is_(None)).order_by(OutboxEventModel.created_at).with_for_update(skip_locked=True).all()