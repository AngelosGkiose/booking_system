from datetime import datetime
from threading import Thread,Barrier

from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.database import SessionLocal
from app.models import VenueModel, SeatModel, EventModel, EventSeatModel, UserModel, ReservationModel
from app.models.eventseat import EventSeatStatus
from app.services.reservation_service import create_reservation_service

results = []
def test_create_reservation_holds_available_event_seat():
    db=SessionLocal()
    try:
        user=UserModel(email="agg@gmail.com",password_hash="123")
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
        reservation=create_reservation_service(event_seat1.id,db,user)
        assert reservation is not None
        assert reservation.event_seat_id == event_seat1.id
        assert event_seat1.status == EventSeatStatus.HELD
    finally:
        db.rollback()
        db.close()


def test_create_reservation_returns_404_when_event_seat_not_found():
    db = SessionLocal()
    try:
        user = UserModel(email="agg@gmail.com", password_hash="123")
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
        with pytest.raises(HTTPException) as exc:
                create_reservation_service(-1, db, user)
        assert exc.value.status_code==404
    finally:
        db.rollback()
        db.close()


def test_create_reservation_returns_409_when_event_seat_is_held():
    db = SessionLocal()
    try:
        user = UserModel(email="agg@gmail.com", password_hash="123")
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
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0,status=EventSeatStatus.HELD)
        db.add(event_seat1)
        db.flush()
        with pytest.raises(HTTPException) as exc:
            create_reservation_service(event_seat1.id, db, user)
        assert exc.value.status_code == 409
    finally:
        db.rollback()
        db.close()


def test_create_reservation_returns_409_when_event_seat_is_reserved():
    db = SessionLocal()
    try:
        user = UserModel(email="agg@gmail.com", password_hash="123")
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
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0, status=EventSeatStatus.RESERVED)
        db.add(event_seat1)
        db.flush()
        with pytest.raises(HTTPException) as exc:
             create_reservation_service(event_seat1.id, db, user)
        assert exc.value.status_code == 409
    finally:
        db.rollback()
        db.close()


def test_create_reservation_rolls_back_on_failure(monkeypatch):
    db = SessionLocal()
    try:
        user = UserModel(email="agg@gmail.com", password_hash="123")
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
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0, status=EventSeatStatus.AVAILABLE)
        db.add(event_seat1)
        db.commit()

        event_seat_id = event_seat1.id
        def fake_commit():
            raise Exception("Commit failed")
        monkeypatch.setattr(db,"commit",fake_commit)

        with pytest.raises(Exception,match="Commit failed"):
            create_reservation_service(event_seat_id, db, user)

        check_db=SessionLocal()
        try:
            saved_event_seat=check_db.query(EventSeatModel).filter(EventSeatModel.id == event_seat_id).first()
            reservation=check_db.query(ReservationModel).filter(ReservationModel.event_seat_id == event_seat_id).all()
            assert saved_event_seat.status==EventSeatStatus.AVAILABLE
            assert len(reservation)==0
        finally:
            check_db.close()
    finally:
        db.rollback()
        db.close()


def test_create_reservation_prevents_double_booking():
    results.clear()
    db = SessionLocal()
    try:
        user1 = UserModel(email="agg@gmail.com", password_hash="123")
        user2=UserModel(email="agg@12321gmail.com", password_hash="123")
        db.add(user1)
        db.flush()
        user1_id=user1.id
        db.add(user2)
        db.flush()
        user2_id=user2.id
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
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0, status=EventSeatStatus.AVAILABLE)
        db.add(event_seat1)
        db.commit()
        event_seat_id = event_seat1.id
        barrier = Barrier(2)
        thread1 = Thread(target=reserve, args=(user1_id,event_seat_id,barrier))
        thread2 = Thread(target=reserve, args=(user2_id,event_seat_id,barrier))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        assert results.count("success") == 1
        assert results.count(409) == 1
        check_db = SessionLocal()
        try:
            saved_event_seat=check_db.query(EventSeatModel).filter(EventSeatModel.id == event_seat_id).first()
            reservations = check_db.query(ReservationModel).filter(
                ReservationModel.event_seat_id == event_seat_id).all()
            assert len(reservations) == 1
            assert saved_event_seat.status==EventSeatStatus.HELD
        finally:
            check_db.close()
    finally:
        db.rollback()
        db.close()


def reserve(user_id,event_seat_id,barrier):
    db=SessionLocal()
    try:
        user=db.query(UserModel).filter(UserModel.id == user_id).first()
        barrier.wait()
        create_reservation_service(event_seat_id,db,user)
        results.append("success")
    except HTTPException as exc:
        results.append(exc.status_code)
    finally:
        db.close()