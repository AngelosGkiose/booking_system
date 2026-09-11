from fastapi import HTTPException
from starlette import status

from app.models import UserModel
from app.repositories.user_repository import get_user_by_email, add_user
from app.security.passwords import hash_password


def register_user(email, password,db):
    try:
        existed_user = get_user_by_email(email,db)
        if existed_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email already registered")
        new_user=UserModel(email=email,hashed_password=hash_password(password))
        add_user(new_user,db)
        db.commit()
        return new_user
    except Exception:
        db.rollback()
        raise