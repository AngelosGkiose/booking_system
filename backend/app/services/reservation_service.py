from datetime import datetime
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
        logger.info("Reservation %s created",reservation.id)
    except HTTPException:
        db.rollback()
        raise
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
        logger.info("Reservation %s confirmed",reservation.id)
        return reservation
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to confirm reservation")
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
        logger.info("Reservation %s cancelled",reservation.id)
        return reservation
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to cancel reservation")
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
        logger.info("Reservation %s got expired",reservation.id)
        return reservation
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to expire reservation")
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
                logger.warning("Skipping reservation %s because event seat %s is not HELD",reservation.id,event_seat.id)
                continue
            reservation.status = ReservationStatus.EXPIRED
            event_seat.status = EventSeatStatus.AVAILABLE
            expired_reservations.append(reservation)
            logger.info("Reservation %s expired", reservation.id)
        db.commit()
        return expired_reservations
    except Exception:
        db.rollback()
        logger.exception("Failed to expire reservation")
        raise

def expire_reservation_background_service(reservation_id, db):
    try:
        reservation = get_reservation_by_id_for_update(reservation_id, db)
        if not reservation:
            logger.debug("Reservation %s not found", reservation_id)
            return
        if reservation.status != ReservationStatus.PENDING:
            logger.debug("Skipping reservation %s because status is %s",reservation.id,reservation.status)
            return
        if reservation.expires_at > datetime.now(ZoneInfo("Europe/Athens")):
            logger.debug(f"Reservation: {reservation_id} has not expired yet")
            return
        event_seat = get_event_seat_for_update(reservation.event_seat_id, db)
        if event_seat.status != EventSeatStatus.HELD:
            logger.warning(f"Event seat {event_seat.id} not held")
            return
        reservation.status = ReservationStatus.EXPIRED
        event_seat.status = EventSeatStatus.AVAILABLE
        db.commit()
        logger.info("Reservation: %s got expired",reservation.id)
    except Exception:
        db.rollback()
        logger.exception("Failed to expire reservation")
        raise
