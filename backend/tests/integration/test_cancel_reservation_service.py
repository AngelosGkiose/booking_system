from datetime import datetime
from threading import Barrier, Thread
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.database import SessionLocal
from app.models import UserModel, VenueModel, SeatModel, EventModel, EventSeatModel
from app.models.eventseat import EventSeatStatus
from app.models.reservation import ReservationStatus, ReservationModel
from app.services.reservation_service import  cancel_reservation_service

results=[]
def test_cancel_reservation_cancels_pending_reservation():
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
        reservation=ReservationModel(event_seat_id=event_seat1.id, user_id=user.id)
        db.add(reservation)
        db.flush()
        cancel_reservation_service(reservation.id,db,user)
        assert reservation.status==ReservationStatus.CANCELED
        assert event_seat1.status==EventSeatStatus.AVAILABLE
    finally:
        db.rollback()
        db.close()

def test_cancel_reservation_returns_404_when_reservation_not_found():
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
        reservation=ReservationModel(event_seat_id=event_seat1.id, user_id=user.id)
        db.add(reservation)
        db.flush()
        with pytest.raises(HTTPException) as exc:
            cancel_reservation_service(-1,db,user)
        assert exc.value.status_code == 404
    finally:
        db.rollback()
        db.close()

def test_cancel_reservation_returns_404_when_reservation_belongs_to_another_user():
    db = SessionLocal()
    try:
        user1 = UserModel(email="agg@gmail.com", password_hash="123")
        db.add(user1)
        db.flush()
        user2= UserModel(email="agg@gmaildsadsa.com", password_hash="123")
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
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0,status=EventSeatStatus.HELD)
        db.add(event_seat1)
        db.flush()
        reservation=ReservationModel(event_seat_id=event_seat1.id, user_id=user1.id)
        db.add(reservation)
        db.flush()
        with pytest.raises(HTTPException) as exc:
            cancel_reservation_service(reservation.id,db,user2)
        assert exc.value.status_code == 404

    finally:
        db.rollback()
        db.close()
def test_cancel_reservation_returns_409_when_reservation_is_not_pending():
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
        reservation=ReservationModel(event_seat_id=event_seat1.id, user_id=user.id,status=ReservationStatus.CANCELED)
        db.add(reservation)
        db.flush()
        with pytest.raises(HTTPException) as exc:
            cancel_reservation_service(reservation.id,db,user)
        assert exc.value.status_code == 409
    finally:
        db.rollback()
        db.close()

def test_cancel_reservation_returns_409_when_event_seat_is_not_held():
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
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0,status=EventSeatStatus.AVAILABLE)
        db.add(event_seat1)
        db.flush()
        reservation=ReservationModel(event_seat_id=event_seat1.id, user_id=user.id,status=ReservationStatus.PENDING)
        db.add(reservation)
        db.flush()
        with pytest.raises(HTTPException) as exc:
            cancel_reservation_service(reservation.id,db,user)
        assert exc.value.status_code == 409
    finally:
        db.rollback()
        db.close()

def test_cancel_reservation_rolls_back_on_failure(monkeypatch):
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
        db.add(event_seat1)
        db.flush()
        event_seat1_id=event_seat1.id
        reservation=ReservationModel(event_seat_id=event_seat1.id, user_id=user.id,status=ReservationStatus.PENDING)
        db.add(reservation)
        db.flush()
        reservation_id = reservation.id
        db.commit()
        def fake_commit():
            raise Exception("Commit failed")
        monkeypatch.setattr(db, "commit", fake_commit)
        with pytest.raises(Exception,match="Commit failed") :
            cancel_reservation_service(reservation.id,db,user)
        check_db=SessionLocal()
        try:
            reservation=check_db.query(ReservationModel).filter(ReservationModel.id==reservation_id).first()
            saved_event_seat1=check_db.query(EventSeatModel).filter(EventSeatModel.id==event_seat1_id).first()
            assert reservation.status==ReservationStatus.PENDING
            assert saved_event_seat1.status==EventSeatStatus.HELD
        finally:
            check_db.close()
    finally:
        db.rollback()
        db.close()

def test_cancel_reservation_prevents_concurrent_cancellation():
    results.clear()
    db = SessionLocal()
    try:
        user1 = UserModel(email="agg@gmail.com", password_hash="123")
        db.add(user1)
        db.flush()
        user1_id = user1.id
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
        event_seat1 = EventSeatModel(seat_id=seat1.id, event_id=event1.id, price=10.0, status=EventSeatStatus.HELD)
        db.add(event_seat1)
        db.flush()
        event_seat1_id = event_seat1.id
        reservation = ReservationModel(event_seat_id=event_seat1.id, user_id=user1.id, status=ReservationStatus.PENDING)
        db.add(reservation)
        db.flush()
        reservation_id = reservation.id
        db.commit()
        barrier=Barrier(2)
        thread1=Thread(target=cancel,args=(reservation_id,user1_id,barrier))
        thread2 = Thread(target=cancel, args=(reservation_id,  user1_id, barrier))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        assert results.count("success") == 1
        assert results.count(409) == 1
        check_db = SessionLocal()
        try:
            reservation=check_db.query(ReservationModel).filter(ReservationModel.id==reservation_id).first()
            saved_event_seat1=check_db.query(EventSeatModel).filter(EventSeatModel.id==event_seat1_id).first()
            assert reservation.status == ReservationStatus.CANCELED
            assert saved_event_seat1.status==EventSeatStatus.AVAILABLE
        finally:
            check_db.close()
    finally:
        db.rollback()
        db.close()


def cancel(reservation_id,user_id,barrier):
    check_db=SessionLocal()
    try:
        user=check_db.query(UserModel).filter(UserModel.id==user_id).first()
        barrier.wait()
        cancel_reservation_service(reservation_id,check_db,user)
        results.append("success")
    except HTTPException as ex:
        results.append(ex.status_code)
    finally:
        check_db.close()