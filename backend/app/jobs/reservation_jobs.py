import logging

from rq import Retry

from app.database import SessionLocal
from app.logging_config import configure_logging
from app.queue import reservation_queue
from app.services.reservation_service import  expire_reservation_background_service

configure_logging()
logger = logging.getLogger(__name__)
def expire_reservation_job(reservation_id):
    db = SessionLocal()
    try:
        reschedule_at = expire_reservation_background_service(reservation_id, db)
        if reschedule_at is not None:
            reservation_queue.enqueue_at(reschedule_at, expire_reservation_job, reservation_id,retry=Retry(max=3, interval=[10, 30, 60]))
    finally:
        db.close()

