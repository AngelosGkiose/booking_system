import logging
from datetime import datetime, timezone, timedelta

from rq import Retry

from app.database import SessionLocal
from app.jobs.reservation_jobs import expire_reservation_job
from app.logging_config import configure_logging
from app.queue import reservation_queue
from app.repositories.outbox_event_repository import get_unprocessed_outbox_event_ids_repo, \
    get_outbox_event_for_update_repo
configure_logging()
logger = logging.getLogger(__name__)
MAX_OUTBOX_ATTEMPTS = 10
def publish_outbox_events_service(db):
    candidate_ids  = get_unprocessed_outbox_event_ids_repo(db)
    for event_id  in candidate_ids:
        process_one_outbox_event(event_id)


def mark_outbox_event_failed_attempt(outbox_event, error_message, max_attempts, db):
    now = datetime.now(timezone.utc)

    outbox_event.attempt_count += 1
    outbox_event.last_error = error_message

    if outbox_event.attempt_count >= max_attempts:
        logger.error(
            "Outbox event %s permanently failed after %s attempts: %s",
            outbox_event.id,
            outbox_event.attempt_count,
            outbox_event.last_error
        )
        outbox_event.failed_at = now
        outbox_event.next_attempt_at = None
    else:
        if outbox_event.attempt_count == 1:
            delay = 10
        elif outbox_event.attempt_count == 2:
            delay = 30
        elif outbox_event.attempt_count == 3:
            delay = 60
        else:
            delay = 300

        outbox_event.next_attempt_at = now + timedelta(seconds=delay)

    db.flush()

    return outbox_event

def process_one_outbox_event(event_id):
    db=SessionLocal()
    try:
        event=get_outbox_event_for_update_repo(event_id,db)
        if not event:
            return
        try:
            if event.event_type != "RESERVATION_CREATED":
                raise ValueError(f"Unsupported outbox event type: {event.event_type}")
            reservation_id = event.payload.get("reservation_id")
            expires_at_str = event.payload.get("expires_at")
            expires_at = datetime.fromisoformat(expires_at_str)
            now = datetime.now(timezone.utc)
            if expires_at <= now:
                reservation_queue.enqueue(expire_reservation_job, reservation_id, retry=Retry(max=3, interval=[10, 30, 60]))
            else:
                logger.info(
                    "Publishing outbox event %s attempt=%s",
                    event.id,
                    event.attempt_count
                )
                reservation_queue.enqueue_at(expires_at, expire_reservation_job, reservation_id,
                                             retry=Retry(max=3, interval=[10, 30, 60]))
        except Exception as exc:
            mark_outbox_event_failed_attempt(event,str(exc),MAX_OUTBOX_ATTEMPTS,db)
            db.commit()
            return
        event.processed_at = datetime.now(timezone.utc)
        event.last_error = None
        db.commit()
    except Exception :
        db.rollback()
        raise
    finally:
        db.close()