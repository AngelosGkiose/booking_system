from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from starlette import status
from uuid import uuid4

from app.config import settings
from app.models import RefreshTokenModel
from app.repositories.refresh_token_repository import add_refresh_token, get_user_refresh_token, \
    get_active_user_sessions_repo, get_user_sessions_repo, get_user_all_sessions_repo
from app.repositories.user_repository import get_user_by_email, get_user_by_id
from app.security.jwt import decode_refresh_token, create_access_token, create_refresh_token
from app.security.passwords import verify_password


def authenticate_user(email, password, db):
    user = get_user_by_email(email,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect email or password")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return user


def refresh_access_token_service(refresh_token:str,db):
    user_id,jti=decode_refresh_token(refresh_token)
    user=get_user_by_id(user_id,db)
    refresh_token_record=get_user_refresh_token(user_id,jti,db)
    if not refresh_token_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate refresh token")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials")
    if refresh_token_record.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")
    if refresh_token_record.expires_at<datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired")
    try:
        refresh_token_record.revoked_at=datetime.now(timezone.utc)
        new_refresh_token=create_refresh_token_service(user_id,db,commit=False)
        access_token = create_access_token({"sub": str(user.id)})
        db.commit()
        return {"access_token":access_token,"refresh_token":new_refresh_token,"token_type":"bearer"}
    except Exception :
        db.rollback()
        raise

def create_refresh_token_service(user_id,db,commit=True):
    data={"sub":str(user_id)}
    jti=str(uuid4())
    exp_time = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expiration_days)
    refresh_token=create_refresh_token(data,jti,exp_time)
    refresh_token_model = RefreshTokenModel(user_id=user_id, jti=jti, expires_at=exp_time)
    add_refresh_token(refresh_token_model, db)
    if commit:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
    return refresh_token

def logout_user_service(refresh_token:str,db):
    user_id,jti=decode_refresh_token(refresh_token)
    user=get_user_by_id(user_id,db)
    refresh_token_record=get_user_refresh_token(user_id,jti,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials")
    if not refresh_token_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate refresh token")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    if refresh_token_record.revoked_at is not None:
        return
    if refresh_token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired")
    try:
        refresh_token_record.revoked_at=datetime.now(timezone.utc)
        db.commit()
        return
    except Exception :
        db.rollback()
        raise

def get_active_sessions_service(user_id,db):
    return get_active_user_sessions_repo(user_id,db)

def delete_user_session_service(session_id,user_id,db):
    refresh_token_record= get_user_sessions_repo(session_id, user_id, db)
    if not refresh_token_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if refresh_token_record.revoked_at is not None:
        return
    try:
        refresh_token_record.revoked_at=datetime.now(timezone.utc)
        db.commit()
        return
    except Exception :
        db.rollback()
        raise

def get_user_all_sessions_service(user_id,db):
    sessions=get_user_all_sessions_repo(user_id,db)
    if not sessions:
        return
    revoked_at = datetime.now(timezone.utc)
    for session in sessions:
        if session.revoked_at is not None:
            continue
        session.revoked_at = revoked_at
    try:
        db.commit()
        return
    except Exception:
        db.rollback()
        raise
