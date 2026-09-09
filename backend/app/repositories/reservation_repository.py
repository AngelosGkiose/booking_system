from app.models import EventSeatModel, ReservationModel
from app.models.reservation import ReservationStatus


def get_event_seat_for_update(event_seat_id,db):
    return db.query(EventSeatModel).filter(EventSeatModel.id == event_seat_id).with_for_update().first()

def add_reservation(reservation,db):
    db.add(reservation)
    return reservation


def get_reservation_for_update(reservation_id,db,user_id,):
    return db.query(ReservationModel).filter(ReservationModel.id == reservation_id,ReservationModel.user_id==user_id).with_for_update().first()

def get_reservation_by_id_for_update(reservation_id,db):
    return db.query(ReservationModel).filter(ReservationModel.id == reservation_id).with_for_update().first()


def get_expired_pending_reservations_for_update(now,db):
    return db.query(ReservationModel).filter(ReservationModel.status==ReservationStatus.PENDING,ReservationModel.expires_at<=now).with_for_update(skip_locked=True).all()