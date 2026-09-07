import pytest
from sqlalchemy import text

from app.database import SessionLocal


@pytest.fixture(autouse=True)
def clean_db():
    db=SessionLocal()
    try:
        db.execute(text("TRUNCATE TABLE users,reservations,venues,seats,events,event_seats Restart IDENTITY CASCADE"))
        db.commit()
        yield
        db.query(text("TRUNCATE TABLE users,reservations,venues,seats,events,event_seats Restart IDENTITY CASCADE"))
        db.commit()
    finally:
        db.close()

