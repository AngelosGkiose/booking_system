from fastapi import HTTPException
from starlette import status

from app.repositories.user_repository import get_user_by_email
from app.security.passwords import verify_password


def authenticate_user(email, password, db):
    user = get_user_by_email(email,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect email or password")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return user

