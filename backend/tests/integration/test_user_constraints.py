import pytest
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import UserModel


def test_user_constraints():
    db = SessionLocal()

    try:
        db.add(UserModel(email="agg@gmail.com", hashed_password="123"))
        db.flush()
        db.add(UserModel(email="agg@gmail.com", hashed_password="1234"))
        with pytest.raises(IntegrityError):
            db.flush()
        print("after second flush")
    finally:
        db.rollback()
        db.close()
