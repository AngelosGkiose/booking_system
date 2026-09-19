from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.database import SessionLocal
from app.models import (
    UserModel,
    VenueModel,
    SeatModel,
    EventModel,
    EventSeatModel,
    IdempotencyRequestModel,
)
from app.models.eventseat import EventSeatStatus
from app.models.idempotencyrequest import IdempotencyRequestEnum
from app.services.reservation_service import create_reservation_service


@pytest.fixture
def reservation_test_data():
    db = SessionLocal()

    try:
        user = UserModel(
            email="idempotency@test.com",
            hashed_password="test-password",
        )
        db.add(user)

        venue = VenueModel(
            name="Idempotency Test Venue",
            address="Test Address",
            city="Athens",
        )
        db.add(venue)

        # Χρειαζόμαστε user.id και venue.id
        db.flush()

        seat_1 = SeatModel(
            venue_id=venue.id,
            section="A",
            row_label="1",
            seat_number=1,
        )

        seat_2 = SeatModel(
            venue_id=venue.id,
            section="A",
            row_label="1",
            seat_number=2,
        )

        db.add_all([seat_1, seat_2])
        db.flush()

        start_time = (
            datetime.now(ZoneInfo("Europe/Athens"))
            + timedelta(days=1)
        )

        event = EventModel(
            venue_id=venue.id,
            name="Idempotency Test Event",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
        )

        db.add(event)
        db.flush()

        event_seat_1 = EventSeatModel(
            event_id=event.id,
            seat_id=seat_1.id,
            status=EventSeatStatus.AVAILABLE,
            price=20.00,
        )

        event_seat_2 = EventSeatModel(
            event_id=event.id,
            seat_id=seat_2.id,
            status=EventSeatStatus.AVAILABLE,
            price=20.00,
        )

        db.add_all([event_seat_1, event_seat_2])
        db.commit()

        db.refresh(user)
        db.refresh(event_seat_1)
        db.refresh(event_seat_2)

        yield {
            "db": db,
            "user": user,
            "venue": venue,
            "event": event,
            "event_seat_1": event_seat_1,
            "event_seat_2": event_seat_2,
        }

    finally:
        db.close()


def test_first_request_creates_reservation(reservation_test_data):
    db = reservation_test_data["db"]
    user = reservation_test_data["user"]
    event_seat = reservation_test_data["event_seat_1"]

    reservation = create_reservation_service(
        key="idempotency-key-1",
        event_seat_id=event_seat.id,
        db=db,
        current_user=user,
    )

    assert reservation is not None
    assert reservation.user_id == user.id
    assert reservation.event_seat_id == event_seat.id

    idempotency_request = (
        db.query(IdempotencyRequestModel)
        .filter(
            IdempotencyRequestModel.user_id == user.id,
            IdempotencyRequestModel.key == "idempotency-key-1",
        )
        .first()
    )

    assert idempotency_request is not None
    assert (
        idempotency_request.status
        == IdempotencyRequestEnum.COMPLETED
    )
    assert idempotency_request.reservation_id == reservation.id
    assert idempotency_request.response_status == 201


def test_same_key_same_request_returns_same_reservation(
    reservation_test_data,
):
    db = reservation_test_data["db"]
    user = reservation_test_data["user"]
    event_seat = reservation_test_data["event_seat_1"]

    first_reservation = create_reservation_service(
        key="idempotency-key-2",
        event_seat_id=event_seat.id,
        db=db,
        current_user=user,
    )

    second_reservation = create_reservation_service(
        key="idempotency-key-2",
        event_seat_id=event_seat.id,
        db=db,
        current_user=user,
    )

    assert first_reservation.id == second_reservation.id

    reservation_count = (
        db.query(type(first_reservation))
        .filter(
            type(first_reservation).event_seat_id == event_seat.id
        )
        .count()
    )

    assert reservation_count == 1


def test_same_key_different_request_returns_409(
    reservation_test_data,
):
    db = reservation_test_data["db"]
    user = reservation_test_data["user"]

    event_seat_1 = reservation_test_data["event_seat_1"]
    event_seat_2 = reservation_test_data["event_seat_2"]

    create_reservation_service(
        key="idempotency-key-3",
        event_seat_id=event_seat_1.id,
        db=db,
        current_user=user,
    )

    with pytest.raises(HTTPException) as exc:
        create_reservation_service(
            key="idempotency-key-3",
            event_seat_id=event_seat_2.id,
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 409

    assert (
        exc.value.detail
        == "Idempotency key already used with different request"
    )


def test_new_key_same_seat_returns_409(
    reservation_test_data,
):
    db = reservation_test_data["db"]
    user = reservation_test_data["user"]
    event_seat = reservation_test_data["event_seat_1"]

    create_reservation_service(
        key="idempotency-key-4",
        event_seat_id=event_seat.id,
        db=db,
        current_user=user,
    )

    with pytest.raises(HTTPException) as exc:
        create_reservation_service(
            key="idempotency-key-5",
            event_seat_id=event_seat.id,
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "Event seat is not available"