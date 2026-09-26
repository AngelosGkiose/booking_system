from app.database import SessionLocal
from app.services.monitoring_service import check_failed_outbox_events_service


def monitor_failed_outbox_events_job():
    db = SessionLocal()
    try:
        check_failed_outbox_events_service(db)
    finally:
        db.close()
