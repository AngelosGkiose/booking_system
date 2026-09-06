from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import UserModel, VenueModel, SeatModel, EventModel, EventSeatModel, ReservationModel
from app.models.reservation import ReservationStatus


def test_reservation_requires_existing_user():
    db=SessionLocal()
    try:
        user = UserModel(email='123@gmail.com', password_hash='123')
        db.add(user)
        db.flush()
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat1 = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        event1 = EventModel(venue_id=venue.id, name="New Event1", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event1)
        db.flush()
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0)
        db.add(event_seat1)
        db.flush()
        db.add(ReservationModel(event_seat_id=event_seat1.id, user_id=-1))
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()



def test_reservation_requires_existing_event_seat():
    db=SessionLocal()
    try:
        user = UserModel(email='123@gmail.com', password_hash='123')
        db.add(user)
        db.flush()
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat1 = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        event1 = EventModel(venue_id=venue.id, name="New Event1", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event1)
        db.flush()
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0)
        db.add(event_seat1)
        db.flush()
        db.add(ReservationModel(event_seat_id=-1, user_id=user.id))
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()

def test_reservation_default_status_is_pending():
    db = SessionLocal()
    try:
        user = UserModel(email='123@gmail.com', password_hash='123')
        db.add(user)
        db.flush()
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat1 = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        event1 = EventModel(venue_id=venue.id, name="New Event1", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event1)
        db.flush()
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0)
        db.add(event_seat1)
        db.flush()
        reservation=ReservationModel(event_seat_id=event_seat1.id, user_id=user.id)
        db.add(reservation)
        db.flush()
        assert reservation.status==ReservationStatus.PENDING
    finally:
        db.rollback()
        db.close()


def test_reservation_expires_at_is_about_ten_minutes_after_created_at():
    db = SessionLocal()
    try:
        user = UserModel(email='123@gmail.com', password_hash='123')
        db.add(user)
        db.flush()
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat1 = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        event1 = EventModel(venue_id=venue.id, name="New Event1", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event1)
        db.flush()
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0)
        db.add(event_seat1)
        db.flush()
        reservation = ReservationModel(event_seat_id=event_seat1.id, user_id=user.id)
        db.add(reservation)
        db.flush()
        difference = reservation.expires_at - reservation.created_at
        assert timedelta(minutes=9, seconds=59) <= difference <= timedelta(minutes=10, seconds=1)
    finally:
        db.rollback()
        db.close()




def test_reservation_relationships():
    db = SessionLocal()
    try:
        user = UserModel(email='123@gmail.com', password_hash='123')
        db.add(user)
        db.flush()
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat1 = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        event1 = EventModel(venue_id=venue.id, name="New Event1", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event1)
        db.flush()
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0)
        db.add(event_seat1)
        db.flush()
        reservation = ReservationModel(event_seat_id=event_seat1.id, user_id=user.id)
        db.add(reservation)
        db.flush()
        assert reservation.user==user
        assert reservation.event_seat==event_seat1
    finally:
        db.rollback()
        db.close()

def test_same_event_seat_allows_multiple_reservations():
    db = SessionLocal()
    try:
        user = UserModel(email='123@gmail.com', password_hash='123')
        db.add(user)
        db.flush()
        user2 = UserModel(email='123@gmaildasdas.coms', password_hash='123')
        db.add(user2)
        db.flush()
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat1 = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        event1 = EventModel(venue_id=venue.id, name="New Event1", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event1)
        db.flush()
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0)
        db.add(event_seat1)
        db.flush()
        reservation = ReservationModel(event_seat_id=event_seat1.id, user_id=user.id,status=ReservationStatus.EXPIRED)
        db.add(reservation)
        db.flush()
        reservation2 = ReservationModel(event_seat_id=event_seat1.id, user_id=user2.id,status=ReservationStatus.PENDING)
        db.add(reservation2)
        db.flush()
    finally:
        db.rollback()
        db.close()


def test_same_user_can_reserve_same_event_seat_again():
    db = SessionLocal()
    try:
        user = UserModel(email='123@gmail.com', password_hash='123')
        db.add(user)
        db.flush()
        user2 = UserModel(email='123@gmaildasdas.coms', password_hash='123')
        db.add(user2)
        db.flush()
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat1 = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        event1 = EventModel(venue_id=venue.id, name="New Event1", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event1)
        db.flush()
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0)
        db.add(event_seat1)
        db.flush()
        reservation = ReservationModel(event_seat_id=event_seat1.id, user_id=user.id,status=ReservationStatus.EXPIRED)
        db.add(reservation)
        db.flush()
        reservation2 = ReservationModel(event_seat_id=event_seat1.id, user_id=user.id,status=ReservationStatus.PENDING)
        db.add(reservation2)
        db.flush()
    finally:
        db.rollback()
        db.close()