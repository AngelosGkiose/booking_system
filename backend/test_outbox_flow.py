from app.database import SessionLocal
from app.models import UserModel
from app.services.reservation_service import create_reservation_service

db = SessionLocal()

try:
    user = db.query(UserModel).first()

    reservation = create_reservation_service(
        key="test-reservation-2", event_seat_id=2, db=db, current_user=user
    )

    print("Reservation created:", reservation.id)

finally:
    db.close()
