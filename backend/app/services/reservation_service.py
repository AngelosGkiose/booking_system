from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from rq import Retry
from fastapi import HTTPException
from starlette import status
from app.queue import reservation_queue
from app.models import ReservationModel
from app.models.eventseat import EventSeatStatus
from app.models.reservation import ReservationStatus
from app.repositories.reservation_repository import get_event_seat_for_update, add_reservation, \
    get_reservation_for_update, get_reservation_by_id_for_update, get_expired_pending_reservations_for_update
import logging

logger = logging.getLogger(__name__)
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
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to create reservation")
        raise
    try:
        from app.jobs.reservation_jobs import expire_reservation_job
        reservation_queue.enqueue_at(reservation.expires_at, expire_reservation_job, reservation.id,retry=Retry(max=3,interval=[10,30,60]))
    except Exception :
        logger.exception("Failed to schedule reservation expiration job")
    return reservation



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
            expired_reservations.append(reservation)
        db.commit()
        return expired_reservations
    except Exception :
        db.rollback()
        raise

def expire_reservation_background_service(reservation_id, db):
    try:
        reservation = get_reservation_by_id_for_update(reservation_id, db)
        if not reservation:
            return
        if reservation.status != ReservationStatus.PENDING:
            return
        if reservation.expires_at > datetime.now(ZoneInfo("Europe/Athens")):
            return
        event_seat = get_event_seat_for_update(reservation.event_seat_id, db)
        if event_seat.status != EventSeatStatus.HELD:
            return
        reservation.status = ReservationStatus.EXPIRED
        event_seat.status = EventSeatStatus.AVAILABLE
        db.commit()
    except Exception:
        db.rollback()
        raise
