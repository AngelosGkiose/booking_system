import pytest
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import UserModel

def test_user_constraints():
    db=SessionLocal()

    try:
        db.add(UserModel(email="agg@gmail.com",password_hash="123"))
        print("before first flush")
        db.flush()
        print("after first flush")
        db.add(UserModel(email="agg@gmail.com",password_hash="1234"))
        print("before second flush")
        with pytest.raises(IntegrityError):
            db.flush()
        print("after second flush")
    finally:
        db.rollback()
        db.close()