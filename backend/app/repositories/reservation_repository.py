from app.models import EventSeatModel


def get_event_seat_for_update(event_seat_id,db):
    return db.query(EventSeatModel).filter(EventSeatModel.id == event_seat_id).with_for_update().first()

def add_reservation(reservation,db):
    db.add(reservation)
    return reservation