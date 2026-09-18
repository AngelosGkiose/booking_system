from fastapi import HTTPException
from starlette import status

from app.queue import redis_connection


def record_failed_login_attempt(client_ip: str):
    key=f"rate_limit:login:ip:{client_ip}"
    count=redis_connection.incr(key)
    if count==1:
        redis_connection.expire(key,60)
    if count>5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail="Too many login requests")


def clear_login_attempts(client_ip: str):
    key = f"rate_limit:login:{client_ip}"
    redis_connection.delete(key)

def record_failed_login_attempt_for_email(email: str):
    email=email.lower()
    key = f"rate_limit:login:email:{email}"
    count=redis_connection.incr(key)
    if count==1:
        redis_connection.expire(key,300)
    if count>5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail="Too many login requests")

def clear_login_attempts_for_email(email: str):
    key = f"rate_limit:login:email:{email.lower()}"
    redis_connection.delete(key)

def check_refresh_rate_limit(client_ip: str):
    key = f"rate_limit:refresh:ip:{client_ip}"
    counter=redis_connection.incr(key)
    if counter==1:
        redis_connection.expire(key,60)
    if counter>20:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail="Too many refresh requests")
