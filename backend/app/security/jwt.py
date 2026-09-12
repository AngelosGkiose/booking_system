from datetime import datetime, timezone, timedelta


import jwt

from app.config import  settings


def create_access_token(data: dict):
    payload=data.copy()
    exp_time=datetime.now(timezone.utc)+ timedelta(minutes=settings.expiration_time)
    payload["exp"]=exp_time
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


