from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import SeatModel, VenueModel, EventSeatModel, EventModel
from app.models.eventseat import EventSeatStatus


def  test_event_seat_requires_existing_event():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat=SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat)
        db.flush()
        event_seat=EventSeatModel(seat_id=seat.id, event_id=-1,price=10.0)
        db.add(event_seat)
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()

def test_event_seat_requires_existing_seat():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        event = EventModel(venue_id=venue.id, name="New Event", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event)
        db.flush()
        event_seat = EventSeatModel(seat_id=-1, event_id=event.id, price=10.0)
        db.add(event_seat)
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()

def test_event_seat_unique_event_and_seat():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat)
        db.flush()
        event = EventModel(venue_id=venue.id, name="New Event", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event)
        db.flush()
        event_seat1 = EventSeatModel(seat_id=seat.id, event_id=event.id, price=10.0)
        db.add(event_seat1)
        db.flush()
        event_seat2=EventSeatModel(seat_id=seat.id, event_id=event.id, price=10.0)
        db.add(event_seat2)
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()

def test_same_seat_allowed_in_different_events():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat)
        db.flush()
        event1 = EventModel(venue_id=venue.id, name="New Event1", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event1)
        db.flush()
        event2 = EventModel(venue_id=venue.id, name="New Event2", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event2)
        db.flush()
        event_seat1 = EventSeatModel(seat_id=seat.id, event_id=event1.id, price=10.0)
        db.add(event_seat1)
        db.flush()
        event_seat2 = EventSeatModel(seat_id=seat.id, event_id=event2.id, price=10.0)
        db.add(event_seat2)
        db.flush()
    finally:
        db.rollback()
        db.close()

def test_same_event_allows_different_seats():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue)
        db.flush()
        seat1 = SeatModel(venue_id=venue.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        seat2 = SeatModel(venue_id=venue.id, section="Main1", row_label="A", seat_number=10)
        db.add(seat2)
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
        event_seat2 = EventSeatModel(seat_id=seat2.id, event_id=event1.id, price=10.0)
        db.add(event_seat2)
        db.flush()
    finally:
        db.rollback()
        db.close()

def test_event_seat_default_status_is_available():
    db=SessionLocal()
    try:
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
        assert event_seat1.status==EventSeatStatus.AVAILABLE
    finally:
        db.rollback()
        db.close()

def test_event_seat_relationships():
    db=SessionLocal()
    try:
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
        assert event_seat1.event == event1
        assert event_seat1.seat == seat1
        assert event_seat1 in event1.event_seats
        assert event_seat1 in seat1.event_seats
    finally:
        db.rollback()
        db.close()
