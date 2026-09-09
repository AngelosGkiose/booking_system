from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


from fastapi import HTTPException
from starlette import status

from app.queue import reservation_queue
from app.models import ReservationModel
from app.models.eventseat import EventSeatStatus
from app.models.reservation import ReservationStatus
from app.repositories.reservation_repository import get_event_seat_for_update, add_reservation, \
    get_reservation_for_update, get_reservation_by_id_for_update, get_expired_pending_reservations_for_update


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
        from app.jobs.reservation_jobs import expire_reservation_job
        reservation_queue.enqueue_at(reservation.expires_at, expire_reservation_job, reservation.id)
        return reservation
    except Exception :
        db.rollback()
        raise

def confirm_reservation_service(reservation_id,db,current_user):
    try:
        reservation=get_reservation_for_update(reservation_id,db,current_user.id)
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Reservation not found")
        if reservation.status !=ReservationStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Reservation  not pending")
        if reservation.expires_at < datetime.now(ZoneInfo("Europe/Athens")):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Reservation  expired")
        event_seat=get_event_seat_for_update(reservation.event_seat_id,db)
        if event_seat.status !=EventSeatStatus.HELD:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Event seat is not Held")
        reservation.status = ReservationStatus.CONFIRMED
        event_seat.status=EventSeatStatus.RESERVED
        db.commit()
        db.refresh(reservation)
        return reservation
    except Exception :
        db.rollback()
        raise

def cancel_reservation_service(reservation_id,db,current_user):
    try:
        reservation=get_reservation_for_update(reservation_id,db,current_user.id)
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Reservation not found")
        if  reservation.status !=ReservationStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Reservation  not pending")
        event_seat = get_event_seat_for_update(reservation.event_seat_id,db)
        if event_seat.status != EventSeatStatus.HELD:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event seat is not Held")
        reservation.status = ReservationStatus.CANCELED
        event_seat.status=EventSeatStatus.AVAILABLE
        event_seat.hold_expires_at = None
        db.commit()
        db.refresh(reservation)
        return reservation
    except Exception :
        db.rollback()
        raise

def expire_reservation_service(reservation_id,db):
    try:
        reservation=get_reservation_by_id_for_update(reservation_id,db)
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Reservation not found")
        if reservation.status !=ReservationStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Reservation  not pending")
        if reservation.expires_at > datetime.now(ZoneInfo("Europe/Athens")):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Reservation is not expired")
        event_seat = get_event_seat_for_update(reservation.event_seat_id,db)
        if event_seat.status !=EventSeatStatus.HELD:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Event seat is not Held")
        reservation.status = ReservationStatus.EXPIRED
        event_seat.status=EventSeatStatus.AVAILABLE
        event_seat.hold_expires_at = None
        db.commit()
        db.refresh(reservation)
        return reservation
    except Exception :
        db.rollback()
        raise

def expire_pending_reservations_service(db):
    expired_reservations=[]
    try:
        reservations=get_expired_pending_reservations_for_update(now=datetime.now(ZoneInfo("Europe/Athens")),db=db)
        if not reservations:
            return []
        for reservation in reservations:
            event_seat = get_event_seat_for_update(reservation.event_seat_id,db)
            if event_seat.status !=EventSeatStatus.HELD:
                continue
            reservation.status = ReservationStatus.EXPIRED
            event_seat.status = EventSeatStatus.AVAILABLE
            event_seat.hold_expires_at = None
            expired_reservations.append(reservation)
        db.commit()
        return expired_reservations
    except Exception :
        db.rollback()
        raise
