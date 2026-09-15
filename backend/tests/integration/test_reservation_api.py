from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import UserModel, VenueModel, SeatModel, EventModel, EventSeatModel, ReservationModel
from app.models.eventseat import EventSeatStatus
from app.models.reservation import ReservationStatus
from app.security.jwt import create_access_token

client = TestClient(app)

def test_user_sees_only_own_reservations():
    db = SessionLocal()
    try:
        user_1 = UserModel(email="user1@test.com", hashed_password="hashed_password")
        user_2 = UserModel(email="user2@test.com", hashed_password="hashed_password")
        db.add_all([user_1, user_2])
        db.flush()

        venue = VenueModel(name="Test Venue", address="Test Address", city="Athens")
        db.add(venue)
        db.flush()

        seat_1 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="1")
        seat_2 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="2")
        seat_3 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="3")
        db.add_all([seat_1, seat_2, seat_3])
        db.flush()

        now = datetime.now(ZoneInfo("Europe/Athens"))

        event = EventModel(venue_id=venue.id, name="Test Event", start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        db.add(event)
        db.flush()

        event_seat_1 = EventSeatModel(event_id=event.id, seat_id=seat_1.id, price=10, status=EventSeatStatus.HELD)
        event_seat_2 = EventSeatModel(event_id=event.id, seat_id=seat_2.id, price=10, status=EventSeatStatus.HELD)
        event_seat_3 = EventSeatModel(event_id=event.id, seat_id=seat_3.id, price=10, status=EventSeatStatus.HELD)
        db.add_all([event_seat_1, event_seat_2, event_seat_3])
        db.flush()

        reservation_1 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_1.id)
        reservation_2 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_2.id)
        reservation_3 = ReservationModel(user_id=user_2.id, event_seat_id=event_seat_3.id)
        db.add_all([reservation_1, reservation_2, reservation_3])
        db.commit()

        token = create_access_token({"sub": str(user_1.id)})

        response = client.get("/reservations/", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200

        data = response.json()

        assert data["total_items"] == 2
        assert len(data["items"]) == 2
        assert all(item["user_id"] == user_1.id for item in data["items"])

    finally:
        db.close()

def test_filter_reservations_by_status():
    db = SessionLocal()
    try:
        user_1 = UserModel(email="user1@test.com", hashed_password="hashed_password")
        user_2 = UserModel(email="user2@test.com", hashed_password="hashed_password")
        db.add_all([user_1, user_2])
        db.flush()

        venue = VenueModel(name="Test Venue", address="Test Address", city="Athens")
        db.add(venue)
        db.flush()

        seat_1 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="1")
        seat_2 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="2")
        seat_3 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="3")
        db.add_all([seat_1, seat_2, seat_3])
        db.flush()

        now = datetime.now(ZoneInfo("Europe/Athens"))

        event = EventModel(venue_id=venue.id, name="Test Event", start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        db.add(event)
        db.flush()

        event_seat_1 = EventSeatModel(event_id=event.id, seat_id=seat_1.id, price=10, status=EventSeatStatus.HELD)
        event_seat_2 = EventSeatModel(event_id=event.id, seat_id=seat_2.id, price=10, status=EventSeatStatus.HELD)
        event_seat_3 = EventSeatModel(event_id=event.id, seat_id=seat_3.id, price=10, status=EventSeatStatus.HELD)
        db.add_all([event_seat_1, event_seat_2, event_seat_3])
        db.flush()

        reservation_1 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_1.id,status=ReservationStatus.PENDING)
        reservation_2 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_2.id,status=ReservationStatus.CONFIRMED)
        reservation_3 = ReservationModel(user_id=user_2.id, event_seat_id=event_seat_3.id,status=ReservationStatus.CANCELED)
        db.add_all([reservation_1, reservation_2, reservation_3])
        db.commit()

        token = create_access_token({"sub": str(user_1.id)})

        response = client.get("/reservations/?reservation_status=CONFIRMED", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200

        data = response.json()

        assert data["total_items"] == 1
        assert len(data["items"]) == 1
        assert all(item["status"] == "CONFIRMED" for item in data["items"])


    finally:
        db.close()

def test_filter_reservations_by_event_id():
    db = SessionLocal()
    try:
        user_1 = UserModel(email="user1@test.com", hashed_password="hashed_password")
        user_2 = UserModel(email="user2@test.com", hashed_password="hashed_password")
        db.add_all([user_1, user_2])
        db.flush()

        venue = VenueModel(name="Test Venue", address="Test Address", city="Athens")
        db.add(venue)
        db.flush()

        seat_1 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="1")
        seat_2 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="2")
        seat_3 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="3")
        db.add_all([seat_1, seat_2, seat_3])
        db.flush()

        now = datetime.now(ZoneInfo("Europe/Athens"))


        event1 = EventModel(venue_id=venue.id, name="Test Event", start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        db.add(event1)
        db.flush()
        event1_id= event1.id
        event2 = EventModel(venue_id=venue.id, name="Test Event12", start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        db.add(event2)
        db.flush()


        event_seat_1 = EventSeatModel(event_id=event1.id, seat_id=seat_1.id, price=10, status=EventSeatStatus.HELD)
        event_seat_2 = EventSeatModel(event_id=event2.id, seat_id=seat_2.id, price=10, status=EventSeatStatus.HELD)
        event_seat_3 = EventSeatModel(event_id=event1.id, seat_id=seat_3.id, price=10, status=EventSeatStatus.HELD)
        db.add_all([event_seat_1, event_seat_2, event_seat_3])
        db.flush()

        reservation_1 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_1.id,status=ReservationStatus.PENDING)
        reservation_2 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_2.id,status=ReservationStatus.CONFIRMED)
        reservation_3 = ReservationModel(user_id=user_2.id, event_seat_id=event_seat_3.id,status=ReservationStatus.CANCELED)
        db.add_all([reservation_1, reservation_2, reservation_3])
        db.commit()

        token = create_access_token({"sub": str(user_1.id)})

        response = client.get(f"/reservations/?event_id={event1_id}", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200

        data = response.json()

        assert data["total_items"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == reservation_1.id


    finally:
        db.close()

def test_reservation_pagination():
    db = SessionLocal()
    try:
        user_1 = UserModel(email="user1@test.com", hashed_password="hashed_password")
        user_2 = UserModel(email="user2@test.com", hashed_password="hashed_password")
        db.add_all([user_1, user_2])
        db.flush()

        venue = VenueModel(name="Test Venue", address="Test Address", city="Athens")
        db.add(venue)
        db.flush()

        seat_1 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="1")
        seat_2 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="2")
        seat_3 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="3")
        seat_4 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="4")
        seat_5 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="5")
        db.add_all([seat_1, seat_2, seat_3,seat_4,seat_5])
        db.flush()

        now = datetime.now(ZoneInfo("Europe/Athens"))

        event = EventModel(venue_id=venue.id, name="Test Event", start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        db.add(event)
        db.flush()

        event_seat_1 = EventSeatModel(event_id=event.id, seat_id=seat_1.id, price=10, status=EventSeatStatus.HELD)
        event_seat_2 = EventSeatModel(event_id=event.id, seat_id=seat_2.id, price=10, status=EventSeatStatus.HELD)
        event_seat_3 = EventSeatModel(event_id=event.id, seat_id=seat_3.id, price=10, status=EventSeatStatus.HELD)
        event_seat_4 = EventSeatModel(event_id=event.id, seat_id=seat_4.id, price=10, status=EventSeatStatus.HELD)
        event_seat_5 = EventSeatModel(event_id=event.id, seat_id=seat_5.id, price=10, status=EventSeatStatus.HELD)
        db.add_all([event_seat_1, event_seat_2, event_seat_3,event_seat_4,event_seat_5])
        db.flush()

        reservation_1 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_1.id,status=ReservationStatus.PENDING)
        reservation_2 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_2.id,status=ReservationStatus.PENDING)
        reservation_3 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_3.id,status=ReservationStatus.PENDING)
        reservation_4 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_4.id,status=ReservationStatus.PENDING)
        reservation_5 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_5.id,status=ReservationStatus.PENDING)
        db.add_all([reservation_1, reservation_2, reservation_3,reservation_4,reservation_5])
        db.commit()

        token = create_access_token({"sub": str(user_1.id)})

        response = client.get("/reservations/?page=2&limit=2", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200

        data = response.json()

        assert data["total_items"] == 5
        assert data["total_pages"] == 3
        assert data["page"] == 2
        assert data["limit"] == 2
        assert len(data["items"]) == 2
        assert data["has_next"] is True
        assert data["has_previous"] is True

    finally:
        db.close()


def test_reservation_sorting():
    db = SessionLocal()
    try:
        user_1 = UserModel(email="user1@test.com", hashed_password="hashed_password")
        user_2 = UserModel(email="user2@test.com", hashed_password="hashed_password")
        db.add_all([user_1, user_2])
        db.flush()

        venue = VenueModel(name="Test Venue", address="Test Address", city="Athens")
        db.add(venue)
        db.flush()

        seat_1 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="1")
        seat_2 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="2")
        seat_3 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="3")
        db.add_all([seat_1, seat_2, seat_3])
        db.flush()

        now = datetime.now(ZoneInfo("Europe/Athens"))

        event = EventModel(venue_id=venue.id, name="Test Event", start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        db.add(event)
        db.flush()

        event_seat_1 = EventSeatModel(event_id=event.id, seat_id=seat_1.id, price=10, status=EventSeatStatus.HELD)
        event_seat_2 = EventSeatModel(event_id=event.id, seat_id=seat_2.id, price=10, status=EventSeatStatus.HELD)
        event_seat_3 = EventSeatModel(event_id=event.id, seat_id=seat_3.id, price=10, status=EventSeatStatus.HELD)
        db.add_all([event_seat_1, event_seat_2, event_seat_3])
        db.flush()

        reservation_1 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_1.id,created_at=now - timedelta(days=2))
        reservation_2 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_2.id,created_at=now - timedelta(days=1))
        reservation_3 = ReservationModel(user_id=user_1.id, event_seat_id=event_seat_3.id,created_at=now)
        db.add_all([reservation_1, reservation_2, reservation_3])
        db.commit()

        token = create_access_token({"sub": str(user_1.id)})

        response = client.get("/reservations/?sort_by=created_at&order=asc", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200

        data = response.json()

        assert data["items"][0]["id"] == reservation_1.id
        assert data["items"][1]["id"] == reservation_2.id
        assert data["items"][2]["id"] == reservation_3.id

        response = client.get("/reservations/?sort_by=created_at&order=desc",headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200

        data = response.json()

        assert data["items"][0]["id"] == reservation_3.id
        assert data["items"][1]["id"] == reservation_2.id
        assert data["items"][2]["id"] == reservation_1.id

    finally:
        db.close()

def test_invalid_sort_by():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token({"sub": str(user.id)})
        response = client.get("/reservations/?sort_by=email", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 400
    finally:
        db.close()


def test_invalid_sort_order():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token({"sub": str(user.id)})
        response = client.get("/reservations/?sort_by=created_at&order=random", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 400
    finally:
        db.close()

def test_filter_reservations_by_date_from():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.flush()

        venue = VenueModel(name="Test Venue", address="Test Address", city="Athens")
        db.add(venue)
        db.flush()

        seat_1 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="1")
        seat_2 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="2")
        seat_3 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="3")
        db.add_all([seat_1, seat_2, seat_3])
        db.flush()

        now = datetime.now(ZoneInfo("Europe/Athens"))

        event = EventModel(venue_id=venue.id, name="Test Event", start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        db.add(event)
        db.flush()

        event_seat_1 = EventSeatModel(event_id=event.id, seat_id=seat_1.id, price=10, status=EventSeatStatus.HELD)
        event_seat_2 = EventSeatModel(event_id=event.id, seat_id=seat_2.id, price=10, status=EventSeatStatus.HELD)
        event_seat_3 = EventSeatModel(event_id=event.id, seat_id=seat_3.id, price=10, status=EventSeatStatus.HELD)
        db.add_all([event_seat_1, event_seat_2, event_seat_3])
        db.flush()

        reservation_1 = ReservationModel(user_id=user.id, event_seat_id=event_seat_1.id, created_at=now - timedelta(days=10))
        reservation_2 = ReservationModel(user_id=user.id, event_seat_id=event_seat_2.id, created_at=now - timedelta(days=5))
        reservation_3 = ReservationModel(user_id=user.id, event_seat_id=event_seat_3.id, created_at=now)
        db.add_all([reservation_1, reservation_2, reservation_3])
        db.commit()

        token = create_access_token({"sub": str(user.id)})
        date_from = (now - timedelta(days=6)).isoformat()

        response = client.get(f"/reservations/?date_from={date_from}", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200

        data = response.json()

        assert data["total_items"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["id"] == reservation_3.id
        assert data["items"][1]["id"] == reservation_2.id

    finally:
        db.close()

def test_filter_reservations_by_date_to():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.flush()

        venue = VenueModel(name="Test Venue", address="Test Address", city="Athens")
        db.add(venue)
        db.flush()

        seat_1 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="1")
        seat_2 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="2")
        seat_3 = SeatModel(venue_id=venue.id, section="A", row_label="1", seat_number="3")
        db.add_all([seat_1, seat_2, seat_3])
        db.flush()

        now = datetime.now(ZoneInfo("Europe/Athens"))

        event = EventModel(venue_id=venue.id, name="Test Event", start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        db.add(event)
        db.flush()

        event_seat_1 = EventSeatModel(event_id=event.id, seat_id=seat_1.id, price=10, status=EventSeatStatus.HELD)
        event_seat_2 = EventSeatModel(event_id=event.id, seat_id=seat_2.id, price=10, status=EventSeatStatus.HELD)
        event_seat_3 = EventSeatModel(event_id=event.id, seat_id=seat_3.id, price=10, status=EventSeatStatus.HELD)
        db.add_all([event_seat_1, event_seat_2, event_seat_3])
        db.flush()

        reservation_1 = ReservationModel(user_id=user.id, event_seat_id=event_seat_1.id, created_at=now - timedelta(days=10))
        reservation_2 = ReservationModel(user_id=user.id, event_seat_id=event_seat_2.id, created_at=now - timedelta(days=5))
        reservation_3 = ReservationModel(user_id=user.id, event_seat_id=event_seat_3.id, created_at=now)
        db.add_all([reservation_1, reservation_2, reservation_3])
        db.commit()

        token = create_access_token({"sub": str(user.id)})
        date_to = (now - timedelta(days=4)).isoformat()

        response = client.get(f"/reservations/?date_to={date_to}", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200

        data = response.json()

        assert data["total_items"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["id"] == reservation_2.id
        assert data["items"][1]["id"] == reservation_1.id

    finally:
        db.close()