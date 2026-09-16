from fastapi import HTTPException
from starlette import status

from app.repositories.user_repository import get_user_by_email, get_user_by_id
from app.security.jwt import decode_refresh_token, create_access_token
from app.security.passwords import verify_password


def authenticate_user(email, password, db):
    user = get_user_by_email(email,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect email or password")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return user


def refresh_access_token_service(refresh_token:str,db):
    user_id=decode_refresh_token(refresh_token)
    user=get_user_by_id(user_id,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token":access_token,"token_type":"bearer"}
