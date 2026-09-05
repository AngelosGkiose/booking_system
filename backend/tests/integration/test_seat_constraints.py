import pytest
from pydantic_settings.sources.providers.nested_secrets import first_not_none
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import SeatModel, VenueModel


def test_seat_requires_existing_venue():
    db=SessionLocal()
    try:
        db.add(SeatModel(venue_id =-1,section="Main",row_label="A",seat_number=10))
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()

def test_seat_unique_constraints():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue", address="Kristal", city="Main City")
        db.add(venue)
        db.flush()
        db.add(SeatModel(venue_id =venue.id,section="Main",row_label="A",seat_number=10))
        db.flush()
        db.add(SeatModel(venue_id =venue.id,section="Main",row_label="A",seat_number=10))
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()


def test_seat_in_different_venues():
    db=SessionLocal()
    try:
        venue1 = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue1)
        db.flush()
        venue2 = VenueModel(name="Main Venue2", address="Kristal2", city="Main City2")
        db.add(venue2)
        db.flush()
        seat1=SeatModel(venue_id=venue1.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        seat2=SeatModel(venue_id=venue2.id, section="Main", row_label="A", seat_number=10)
        db.add(seat2)
        db.flush()
        assert seat1.id is not None
        assert seat2.id is not None
        assert seat1.id != seat2.id
    finally:
        db.rollback()
        db.close()

def test_seat_venue_relationship():
    db=SessionLocal()
    try:
        venue1 = VenueModel(name="Main Venue1", address="Kristal1", city="Main City1")
        db.add(venue1)
        db.flush()
        seat1 = SeatModel(venue_id=venue1.id, section="Main", row_label="A", seat_number=10)
        db.add(seat1)
        db.flush()
        assert venue1.seats is not None
        assert seat1.venue is not None
    finally:
        db.rollback()
        db.close()
