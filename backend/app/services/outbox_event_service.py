from datetime import datetime, timezone

from rq import Retry

from app.jobs.reservation_jobs import expire_reservation_job
from app.queue import reservation_queue
from app.repositories.outbox_event_repository import get_unprocessed_outbox_events_repo


def publish_outbox_events_service(db):
    events = get_unprocessed_outbox_events_repo(db)
    try:
        for event in events:
            if event.event_type == "RESERVATION_CREATED":
                reservation_id = event.payload.get("reservation_id")
                expires_at_str = event.payload.get("expires_at")
                expires_at = datetime.fromisoformat(expires_at_str)
                now = datetime.now(timezone.utc)
                if expires_at <= now:
                    reservation_queue.enqueue(expire_reservation_job, reservation_id,retry=Retry(max=3, interval=[10, 30, 60]))
                else:
                    reservation_queue.enqueue_at(expires_at, expire_reservation_job, reservation_id,retry=Retry(max=3,interval=[10,30,60]))
                event.processed_at = now
        db.commit()
    except Exception:
        db.rollback()
        raise