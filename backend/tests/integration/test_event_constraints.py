from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import VenueModel, EventModel


def test_event_existing_venue():
    db=SessionLocal()
    try:
        db.add(EventModel(venue_id=-1,name="New Event",start_time = datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")),end_time = datetime(
    2026, 9, 10, 22, 0,
    tzinfo=ZoneInfo("Europe/Athens")
        )))
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()

def test_event_unique_constraints():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue", address="Kristal", city="Main City")
        db.add(venue)
        db.flush()
        db.add(EventModel(venue_id=venue.id, name="New Event", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        )))
        db.flush()
        db.add(EventModel(venue_id=venue.id, name="New Event", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        )))
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()

def test_end_after_start():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue", address="Kristal", city="Main City")
        db.add(venue)
        db.flush()
        db.add(EventModel(venue_id=venue.id, name="New Event", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 19, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        )))
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()

def test_event_diff_start():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue", address="Kristal", city="Main City")
        db.add(venue)
        db.flush()
        db.add(EventModel(venue_id=venue.id, name="New Event", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        )))
        db.flush()
        db.add(EventModel(venue_id=venue.id, name="New Event", start_time=datetime(
            2026, 10, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 10, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        )))
        db.flush()
    finally:
        db.rollback()
        db.close()

def test_event_venue_relationship():
    db=SessionLocal()
    try:
        venue = VenueModel(name="Main Venue", address="Kristal", city="Main City")
        db.add(venue)
        db.flush()
        event=EventModel(venue_id=venue.id, name="New Event", start_time=datetime(
            2026, 9, 10, 20, 0,
            tzinfo=ZoneInfo("Europe/Athens")), end_time=datetime(
            2026, 9, 10, 22, 0,
            tzinfo=ZoneInfo("Europe/Athens")
        ))
        db.add(event)
        db.flush()
        assert venue.events is not None
        assert event.venue is not None
        assert event.venue == venue
        assert event in venue.events
    finally:
        db.rollback()
        db.close()
