import logging
from time import sleep

from app.database import SessionLocal
from app.logging_config import configure_logging
from app.services.outbox_event_service import publish_outbox_events_service

configure_logging()
logger = logging.getLogger(__name__)


def run_worker():
    logger.info("Outbox publisher worker started")
    while True:
        db = SessionLocal()
        try:
            publish_outbox_events_service(db)
        except Exception:
            logger.exception("Outbox publishing failed")
        finally:
            db.close()
        sleep(5)


if __name__ == "__main__":
    run_worker()
