from app.models import EventSeatModel, ReservationModel
from app.models.reservation import ReservationStatus


def get_event_seat_for_update(event_seat_id, db):
    return (
        db.query(EventSeatModel)
        .filter(EventSeatModel.id == event_seat_id)
        .with_for_update()
        .first()
    )


def add_reservation(reservation, db):
    db.add(reservation)
    db.flush()
    return reservation


def get_reservation_for_update(
    reservation_id,
    db,
    user_id,
):
    return (
        db.query(ReservationModel)
        .filter(
            ReservationModel.id == reservation_id, ReservationModel.user_id == user_id
        )
        .with_for_update()
        .first()
    )


def get_reservation_by_id_for_update(reservation_id, db):
    return (
        db.query(ReservationModel)
        .filter(ReservationModel.id == reservation_id)
        .with_for_update()
        .first()
    )


def get_reservation_by_id_repo(reservation_id, db):
    return (
        db.query(ReservationModel).filter(ReservationModel.id == reservation_id).first()
    )


def get_user_reservation_by_id_repo(reservation_id, current_user_id, db):
    return (
        db.query(ReservationModel)
        .filter(
            ReservationModel.id == reservation_id,
            ReservationModel.user_id == current_user_id,
        )
        .first()
    )


def get_expired_pending_reservations_for_update(now, db):
    return (
        db.query(ReservationModel)
        .filter(
            ReservationModel.status == ReservationStatus.PENDING,
            ReservationModel.expires_at <= now,
        )
        .with_for_update(skip_locked=True)
        .all()
    )


def get_user_reservations_repo(
    sort_by,
    order,
    event_id,
    reservation_status,
    date_from,
    date_to,
    skip,
    limit,
    current_user_id,
    db,
):
    query = (
        db.query(ReservationModel)
        .join(EventSeatModel, ReservationModel.event_seat_id == EventSeatModel.id)
        .filter(ReservationModel.user_id == current_user_id)
    )
    if event_id is not None:
        query = query.filter(EventSeatModel.event_id == event_id)
    if reservation_status is not None:
        query = query.filter(ReservationModel.status == reservation_status)
    if date_from is not None:
        query = query.filter(ReservationModel.created_at >= date_from)
    if date_to is not None:
        query = query.filter(ReservationModel.created_at <= date_to)

    sort_columns = {
        "created_at": ReservationModel.created_at,
        "expires_at": ReservationModel.expires_at,
    }
    sort_column = sort_columns[sort_by]
    if order == "desc":
        order_expression = sort_column.desc()
    else:
        order_expression = sort_column.asc()

    return query.order_by(order_expression).offset(skip).limit(limit).all()


def count_user_reservations_repo(
    event_id, reservation_status, date_from, date_to, current_user_id, db
):
    query = (
        db.query(ReservationModel)
        .join(EventSeatModel, ReservationModel.event_seat_id == EventSeatModel.id)
        .filter(ReservationModel.user_id == current_user_id)
    )
    if event_id is not None:
        query = query.filter(EventSeatModel.event_id == event_id)
    if reservation_status is not None:
        query = query.filter(ReservationModel.status == reservation_status)
    if date_from is not None:
        query = query.filter(ReservationModel.created_at >= date_from)
    if date_to is not None:
        query = query.filter(ReservationModel.created_at <= date_to)
    return query.count()
