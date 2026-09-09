from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.database import SessionLocal
from app.models import UserModel, VenueModel, SeatModel, EventModel, EventSeatModel, ReservationModel
from app.models.eventseat import EventSeatStatus
from app.models.reservation import ReservationStatus
from app.services.reservation_service import expire_pending_reservations_service


def test_expire_pending_reservations_expires_all_valid_expired_reservations():
    db = SessionLocal()

    try:
        user = UserModel(
            email="agg@gmail.com",
            password_hash="123"
        )
        db.add(user)
        db.flush()

        venue = VenueModel(
            name="Main Venue1",
            address="Kristal1",
            city="Main City1"
        )
        db.add(venue)
        db.flush()

        seat1 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=10
        )

        seat2 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=11
        )

        db.add_all([seat1, seat2])
        db.flush()

        event = EventModel(
            venue_id=venue.id,
            name="New Event1",
            start_time=datetime(
                2026, 9, 10, 20, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            ),
            end_time=datetime(
                2026, 9, 10, 22, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            )
        )

        db.add(event)
        db.flush()

        event_seat1 = EventSeatModel(
            seat_id=seat1.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        event_seat2 = EventSeatModel(
            seat_id=seat2.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        db.add_all([event_seat1, event_seat2])
        db.flush()

        reservation1 = ReservationModel(
            event_seat_id=event_seat1.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        reservation2 = ReservationModel(
            event_seat_id=event_seat2.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=2)
        )

        db.add_all([reservation1, reservation2])
        db.flush()

        expired_reservations = expire_pending_reservations_service(db)

        assert len(expired_reservations) == 2

        assert reservation1.status == ReservationStatus.EXPIRED
        assert reservation2.status == ReservationStatus.EXPIRED

        assert event_seat1.status == EventSeatStatus.AVAILABLE
        assert event_seat2.status == EventSeatStatus.AVAILABLE

        assert event_seat1.hold_expires_at is None
        assert event_seat2.hold_expires_at is None

    finally:
        db.rollback()
        db.close()

def test_expire_pending_reservations_returns_empty_when_none_expired():
    db = SessionLocal()

    try:
        user = UserModel(
            email="agg@gmail.com",
            password_hash="123"
        )
        db.add(user)
        db.flush()

        venue = VenueModel(
            name="Main Venue1",
            address="Kristal1",
            city="Main City1"
        )
        db.add(venue)
        db.flush()

        seat1 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=10
        )

        seat2 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=11
        )

        db.add_all([seat1, seat2])
        db.flush()

        event = EventModel(
            venue_id=venue.id,
            name="New Event1",
            start_time=datetime(
                2026, 9, 10, 20, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            ),
            end_time=datetime(
                2026, 9, 10, 22, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            )
        )

        db.add(event)
        db.flush()

        event_seat1 = EventSeatModel(
            seat_id=seat1.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        event_seat2 = EventSeatModel(
            seat_id=seat2.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        db.add_all([event_seat1, event_seat2])
        db.flush()

        reservation1 = ReservationModel(
            event_seat_id=event_seat1.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) + timedelta(minutes=1)
        )

        reservation2 = ReservationModel(
            event_seat_id=event_seat2.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) + timedelta(minutes=2)
        )

        db.add_all([reservation1, reservation2])
        db.flush()

        expired_reservations = expire_pending_reservations_service(db)

        assert len(expired_reservations) == 0
    finally:
        db.rollback()
        db.close()

def test_expire_pending_reservations_skips_event_seat_not_held():
    db = SessionLocal()

    try:
        user = UserModel(
            email="agg@gmail.com",
            password_hash="123"
        )
        db.add(user)
        db.flush()

        venue = VenueModel(
            name="Main Venue1",
            address="Kristal1",
            city="Main City1"
        )
        db.add(venue)
        db.flush()

        seat1 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=10
        )

        seat2 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=11
        )

        db.add_all([seat1, seat2])
        db.flush()

        event = EventModel(
            venue_id=venue.id,
            name="New Event1",
            start_time=datetime(
                2026, 9, 10, 20, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            ),
            end_time=datetime(
                2026, 9, 10, 22, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            )
        )

        db.add(event)
        db.flush()

        event_seat1 = EventSeatModel(
            seat_id=seat1.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        event_seat2 = EventSeatModel(
            seat_id=seat2.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.RESERVED,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        db.add_all([event_seat1, event_seat2])
        db.flush()

        reservation1 = ReservationModel(
            event_seat_id=event_seat1.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        reservation2 = ReservationModel(
            event_seat_id=event_seat2.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=2)
        )

        db.add_all([reservation1, reservation2])
        db.flush()

        expired_reservations = expire_pending_reservations_service(db)

        assert len(expired_reservations) == 1
        assert reservation1.status == ReservationStatus.EXPIRED
        assert reservation2.status == ReservationStatus.PENDING

        assert event_seat1.status == EventSeatStatus.AVAILABLE
        assert event_seat2.status == EventSeatStatus.RESERVED

        assert event_seat1.hold_expires_at is None
        assert event_seat2.hold_expires_at is not None
    finally:
        db.rollback()
        db.close()

def test_expire_pending_reservations_ignores_non_pending_reservations():
    db = SessionLocal()

    try:
        user = UserModel(
            email="agg@gmail.com",
            password_hash="123"
        )
        db.add(user)
        db.flush()

        venue = VenueModel(
            name="Main Venue1",
            address="Kristal1",
            city="Main City1"
        )
        db.add(venue)
        db.flush()

        seat1 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=10
        )

        seat2 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=11
        )

        db.add_all([seat1, seat2])
        db.flush()

        event = EventModel(
            venue_id=venue.id,
            name="New Event1",
            start_time=datetime(
                2026, 9, 10, 20, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            ),
            end_time=datetime(
                2026, 9, 10, 22, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            )
        )

        db.add(event)
        db.flush()

        event_seat1 = EventSeatModel(
            seat_id=seat1.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        event_seat2 = EventSeatModel(
            seat_id=seat2.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        db.add_all([event_seat1, event_seat2])
        db.flush()

        reservation1 = ReservationModel(
            event_seat_id=event_seat1.id,
            user_id=user.id,
            status=ReservationStatus.CONFIRMED,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        reservation2 = ReservationModel(
            event_seat_id=event_seat2.id,
            user_id=user.id,
            status=ReservationStatus.CONFIRMED,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=2)
        )

        db.add_all([reservation1, reservation2])
        db.flush()

        expired_reservations = expire_pending_reservations_service(db)

        assert len(expired_reservations) == 0
        assert reservation1.status == ReservationStatus.CONFIRMED
        assert reservation2.status == ReservationStatus.CONFIRMED

        assert event_seat1.status == EventSeatStatus.HELD
        assert event_seat2.status == EventSeatStatus.HELD
        assert event_seat1.hold_expires_at is not None
        assert event_seat2.hold_expires_at is not None
    finally:
        db.rollback()
        db.close()

def test_expire_pending_reservations_rolls_back_on_failure(monkeypatch):
    db = SessionLocal()

    try:
        user = UserModel(
            email="agg@gmail.com",
            password_hash="123"
        )
        db.add(user)
        db.flush()

        venue = VenueModel(
            name="Main Venue1",
            address="Kristal1",
            city="Main City1"
        )
        db.add(venue)
        db.flush()

        seat1 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=10
        )

        seat2 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=11
        )

        db.add_all([seat1, seat2])
        db.flush()

        event = EventModel(
            venue_id=venue.id,
            name="New Event1",
            start_time=datetime(
                2026, 9, 10, 20, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            ),
            end_time=datetime(
                2026, 9, 10, 22, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            )
        )

        db.add(event)
        db.flush()

        event_seat1 = EventSeatModel(
            seat_id=seat1.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        event_seat2 = EventSeatModel(
            seat_id=seat2.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        db.add_all([event_seat1, event_seat2])
        db.flush()
        event_seat1_id=event_seat1.id
        event_seat2_id=event_seat2.id

        reservation1 = ReservationModel(
            event_seat_id=event_seat1.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        reservation2 = ReservationModel(
            event_seat_id=event_seat2.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=2)
        )
        db.add_all([reservation1, reservation2])
        db.flush()
        reservation1_id=reservation1.id
        reservation2_id=reservation2.id
        db.commit()
        def fake_commit():
            raise Exception("Commit failed")
        monkeypatch.setattr(db, "commit", fake_commit)
        with pytest.raises(Exception,match="Commit failed"):
             expire_pending_reservations_service(db)
        check_db=SessionLocal()
        try:
            reservation1=check_db.query(ReservationModel).filter(ReservationModel.id==reservation1_id).first()
            reservation2 = check_db.query(ReservationModel).filter(ReservationModel.id == reservation2_id).first()
            saved_event_seat1=check_db.query(EventSeatModel).filter(EventSeatModel.id==event_seat1_id).first()
            saved_event_seat2 = check_db.query(EventSeatModel).filter(EventSeatModel.id == event_seat2_id).first()
            assert reservation1.status==ReservationStatus.PENDING
            assert reservation2.status == ReservationStatus.PENDING
            assert saved_event_seat1.status==EventSeatStatus.HELD
            assert saved_event_seat2.status == EventSeatStatus.HELD
            assert saved_event_seat1.hold_expires_at is not None
            assert saved_event_seat2.hold_expires_at is not None
        finally:
            check_db.close()
    finally:
        db.rollback()
        db.close()

def test_expire_pending_reservations_uses_skip_locked():
    db = SessionLocal()

    try:
        user = UserModel(
            email="agg@gmail.com",
            password_hash="123"
        )
        db.add(user)
        db.flush()

        venue = VenueModel(
            name="Main Venue1",
            address="Kristal1",
            city="Main City1"
        )
        db.add(venue)
        db.flush()

        seat1 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=10
        )

        seat2 = SeatModel(
            venue_id=venue.id,
            section="Main",
            row_label="A",
            seat_number=11
        )

        db.add_all([seat1, seat2])
        db.flush()

        event = EventModel(
            venue_id=venue.id,
            name="New Event1",
            start_time=datetime(
                2026, 9, 10, 20, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            ),
            end_time=datetime(
                2026, 9, 10, 22, 0,
                tzinfo=ZoneInfo("Europe/Athens")
            )
        )

        db.add(event)
        db.flush()

        event_seat1 = EventSeatModel(
            seat_id=seat1.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        event_seat2 = EventSeatModel(
            seat_id=seat2.id,
            event_id=event.id,
            price=10.0,
            status=EventSeatStatus.HELD,
            hold_expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        db.add_all([event_seat1, event_seat2])
        db.flush()
        event_seat1_id=event_seat1.id
        event_seat2_id=event_seat2.id

        reservation1 = ReservationModel(
            event_seat_id=event_seat1.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=1)
        )

        reservation2 = ReservationModel(
            event_seat_id=event_seat2.id,
            user_id=user.id,
            status=ReservationStatus.PENDING,
            expires_at=datetime.now(
                ZoneInfo("Europe/Athens")
            ) - timedelta(minutes=2)
        )
        db.add_all([reservation1, reservation2])
        db.flush()
        reservation1_id=reservation1.id
        reservation2_id=reservation2.id
        db.commit()
        worker1_db = SessionLocal()
        worker2_db = SessionLocal()
        worker1_db.query(ReservationModel).filter(ReservationModel.id == reservation1_id,ReservationModel.status == ReservationStatus.PENDING,
                                      ReservationModel.expires_at <= datetime.now(ZoneInfo("Europe/Athens"))).with_for_update().first()
        results=expire_pending_reservations_service(worker2_db)
        assert len(results) == 1
        assert results[0].id == reservation2_id
        worker1_db.rollback()
        check_db=SessionLocal()
        try:
            reservation1=check_db.query(ReservationModel).filter(ReservationModel.id==reservation1_id).first()
            reservation2 = check_db.query(ReservationModel).filter(ReservationModel.id == reservation2_id).first()
            saved_event_seat1=check_db.query(EventSeatModel).filter(EventSeatModel.id==event_seat1_id).first()
            saved_event_seat2 = check_db.query(EventSeatModel).filter(EventSeatModel.id == event_seat2_id).first()
            assert reservation1.status==ReservationStatus.PENDING
            assert reservation2.status == ReservationStatus.EXPIRED
            assert saved_event_seat1.status==EventSeatStatus.HELD
            assert saved_event_seat2.status == EventSeatStatus.AVAILABLE
            assert saved_event_seat1.hold_expires_at is not None
            assert saved_event_seat2.hold_expires_at is  None
        finally:
            check_db.close()
            worker1_db.close()
            worker2_db.close()
    finally:
        db.rollback()
        db.close()
