import logging
from datetime import datetime
from math import ceil
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from starlette import status

from app.models import OutboxEventModel, ReservationModel
from app.models.eventseat import EventSeatStatus
from app.models.idempotencyrequest import IdempotencyRequestEnum
from app.models.reservation import ReservationStatus
from app.repositories.outbox_event_repository import create_outbox_event_repo
from app.repositories.reservation_repository import (
    add_reservation,
    count_user_reservations_repo,
    get_event_seat_for_update,
    get_expired_pending_reservations_for_update,
    get_reservation_by_id_for_update,
    get_reservation_by_id_repo,
    get_reservation_for_update,
    get_user_reservation_by_id_repo,
    get_user_reservations_repo,
)
from app.services.idempotency_service import (
    create_idempotency_request,
    mark_idempotency_completed,
    mark_idempotency_failed,
)
from app.services.utils.hashing import generate_request_hash

logger = logging.getLogger(__name__)


def create_reservation_service(key, event_seat_id, db, current_user):
    try:
        request_hash = generate_request_hash(event_seat_id)
        idempotency_request = create_idempotency_request(
            current_user.id, key, request_hash, db
        )
        if idempotency_request.status == IdempotencyRequestEnum.COMPLETED:
            reservation = get_reservation_by_id_repo(
                idempotency_request.reservation_id, db
            )
            if reservation is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Inconsistent idempotency state",
                )
            return reservation
        event_seat = get_event_seat_for_update(event_seat_id, db)
        if not event_seat:
            mark_idempotency_failed(
                idempotency_request, 404, "Event seat not found", db
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event seat not found"
            )
        if event_seat.status != EventSeatStatus.AVAILABLE:
            mark_idempotency_failed(
                idempotency_request, 409, "Event seat is not available", db
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Event seat is not available",
            )
        reservation = ReservationModel(
            user_id=current_user.id, event_seat_id=event_seat.id
        )
        add_reservation(reservation, db)
        event_seat.status = EventSeatStatus.HELD
        create_outbox_event_repo(
            OutboxEventModel(
                event_type="RESERVATION_CREATED",
                payload={
                    "reservation_id": reservation.id,
                    "expires_at": reservation.expires_at.isoformat(),
                },
            ),
            db,
        )
        mark_idempotency_completed(idempotency_request, reservation.id, 201, db)
        db.commit()
        logger.info("Reservation %s created", reservation.id)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to create reservation")
        raise
    return reservation


def confirm_reservation_service(reservation_id, db, current_user):
    try:
        reservation = get_reservation_for_update(reservation_id, db, current_user.id)
        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
            )
        if reservation.status != ReservationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Reservation  not pending"
            )
        if reservation.expires_at < datetime.now(ZoneInfo("Europe/Athens")):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Reservation  expired"
            )
        event_seat = get_event_seat_for_update(reservation.event_seat_id, db)
        if event_seat.status != EventSeatStatus.HELD:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Event seat is not Held"
            )
        reservation.status = ReservationStatus.CONFIRMED
        event_seat.status = EventSeatStatus.RESERVED
        db.commit()
        db.refresh(reservation)
        logger.info("Reservation %s confirmed", reservation.id)
        return reservation
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to confirm reservation")
        raise


def cancel_reservation_service(reservation_id, db, current_user):
    try:
        reservation = get_reservation_for_update(reservation_id, db, current_user.id)
        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
            )
        if reservation.status != ReservationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Reservation  not pending"
            )
        event_seat = get_event_seat_for_update(reservation.event_seat_id, db)
        if event_seat.status != EventSeatStatus.HELD:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Event seat is not Held"
            )
        reservation.status = ReservationStatus.CANCELED
        event_seat.status = EventSeatStatus.AVAILABLE
        db.commit()
        db.refresh(reservation)
        logger.info("Reservation %s cancelled", reservation.id)
        return reservation
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to cancel reservation")
        raise


def expire_reservation_service(reservation_id, db):
    try:
        reservation = get_reservation_by_id_for_update(reservation_id, db)
        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
            )
        if reservation.status != ReservationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Reservation  not pending"
            )
        if reservation.expires_at > datetime.now(ZoneInfo("Europe/Athens")):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Reservation is not expired",
            )
        event_seat = get_event_seat_for_update(reservation.event_seat_id, db)
        if event_seat.status != EventSeatStatus.HELD:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Event seat is not Held"
            )
        reservation.status = ReservationStatus.EXPIRED
        event_seat.status = EventSeatStatus.AVAILABLE
        db.commit()
        db.refresh(reservation)
        logger.info("Reservation %s got expired", reservation.id)
        return reservation
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to expire reservation")
        raise


def expire_pending_reservations_service(db):
    expired_reservations = []
    try:
        reservations = get_expired_pending_reservations_for_update(
            now=datetime.now(ZoneInfo("Europe/Athens")), db=db
        )
        if not reservations:
            return []
        for reservation in reservations:
            event_seat = get_event_seat_for_update(reservation.event_seat_id, db)
            if event_seat.status != EventSeatStatus.HELD:
                logger.warning(
                    "Skipping reservation %s because event seat %s is not HELD",
                    reservation.id,
                    event_seat.id,
                )
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
            return None
        if reservation.status != ReservationStatus.PENDING:
            logger.debug(
                "Skipping reservation %s because status is %s",
                reservation.id,
                reservation.status,
            )
            return None
        if reservation.expires_at > datetime.now(ZoneInfo("Europe/Athens")):
            logger.info(
                "Reservation %s executed too early, reschedule at %s",
                reservation.id,
                reservation.expires_at,
            )
            logger.debug(f"Reservation: {reservation_id} has not expired yet")
            return reservation.expires_at
        event_seat = get_event_seat_for_update(reservation.event_seat_id, db)
        if event_seat.status != EventSeatStatus.HELD:
            logger.warning(f"Event seat {event_seat.id} not held")
            return None
        reservation.status = ReservationStatus.EXPIRED
        event_seat.status = EventSeatStatus.AVAILABLE
        db.commit()
        logger.info("Reservation: %s got expired", reservation.id)
        return None
    except Exception:
        db.rollback()
        logger.exception("Failed to expire reservation")
        raise


def get_user_reservations_service(
    sort_by,
    order,
    event_id,
    reservation_status,
    date_from,
    date_to,
    page,
    limit,
    current_user,
    db,
):
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must be before date_to",
        )

    allowed_sort_fields = {"created_at", "expires_at"}

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort_by value"
        )

    allowed_orders = {"asc", "desc"}

    if order not in allowed_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order value"
        )

    skip = (page - 1) * limit
    total_items = count_user_reservations_repo(
        event_id, reservation_status, date_from, date_to, current_user.id, db
    )
    total_pages = ceil(total_items / limit)
    items = get_user_reservations_repo(
        sort_by,
        order,
        event_id,
        reservation_status,
        date_from,
        date_to,
        skip,
        limit,
        current_user.id,
        db,
    )
    has_next = page < total_pages
    has_previous = page > 1

    return {
        "items": items,
        "total_items": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous,
    }


def get_user_reservation_by_id_service(reservation_id, db, current_user):
    reservation = get_user_reservation_by_id_repo(reservation_id, current_user.id, db)
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
        )
    return reservation
