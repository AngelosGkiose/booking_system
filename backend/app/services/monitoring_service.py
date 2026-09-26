import logging

from app.logging_config import configure_logging
from app.repositories.outbox_event_repository import get_failed_outbox_events_count_repo

configure_logging()
logger = logging.getLogger(__name__)


def check_failed_outbox_events_service(db):
    failed_count = get_failed_outbox_events_count_repo(db)

    if failed_count == 0:
        logger.info("No failed outbox events found")
    else:
        logger.warning("Failed outbox events found: %s", failed_count)


def monitoring_outbox_service(db):
    failed_count = get_failed_outbox_events_count_repo(db)
    return {"failed_outbox_events": failed_count}
