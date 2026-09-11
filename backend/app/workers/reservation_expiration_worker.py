from time import sleep
from app.database import SessionLocal
from app.logging_config import configure_logging
from app.services.reservation_service import expire_pending_reservations_service
import logging

configure_logging()
logger = logging.getLogger(__name__)
def run_worker():
    logger.info("Reservation expiration polling worker started")
    while True:
        logger.debug("Checking for expired reservations")
        db=SessionLocal()
        try:
            expire_pending_reservations_service(db)
        except Exception :
            logger.exception("Reservation expiration polling failed")
        finally:
            db.close()
        sleep(30)


if __name__ == "__main__":
    run_worker()