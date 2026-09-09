from app.database import SessionLocal
from app.services.reservation_service import expire_reservation_service


def expire_reservation_job(reservation_id):
    db = SessionLocal()
    try:
        return  expire_reservation_service(reservation_id, db)
    finally:
        db.close()

