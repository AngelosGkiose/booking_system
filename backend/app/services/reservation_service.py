from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from starlette import status

from app.models import ReservationModel
from app.models.eventseat import EventSeatStatus
from app.repositories.reservation_repository import get_event_seat_for_update, add_reservation


def create_reservation_service(event_seat_id,db,current_user):
    try:
        event_seat=get_event_seat_for_update(event_seat_id,db)
        if not event_seat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Event seat not found")
        if event_seat.status!=EventSeatStatus.AVAILABLE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Event seat is not available")
        reservation=ReservationModel(user_id=current_user.id,event_seat_id=event_seat.id)
        add_reservation(reservation,db)
        event_seat.status=EventSeatStatus.HELD
        event_seat.hold_expires_at=datetime.now(ZoneInfo("Europe/Athens")) + timedelta(minutes=10)
        db.commit()
        db.refresh(reservation)
        return reservation
    except Exception :
        db.rollback()
        raise

