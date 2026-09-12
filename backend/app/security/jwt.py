from datetime import datetime, timezone, timedelta


import jwt
from fastapi import HTTPException
from starlette import status

from app.config import  settings


def create_access_token(data: dict):
    payload=data.copy()
    exp_time=datetime.now(timezone.utc)+ timedelta(minutes=settings.expiration_time)
    payload["exp"]=exp_time
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token):
    try:
        payload=jwt.decode(token, settings.secret_key, algorithm=[settings.algorithm])
        user_id=payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


