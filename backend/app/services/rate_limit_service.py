from fastapi import HTTPException
from starlette import status

from app.queue import redis_connection


def clear_rate_limit(key):
    redis_connection.delete(key)


def record_rate_limit_attempt(key, limit, window_seconds):
    counter = redis_connection.incr(key)
    if counter == 1:
        redis_connection.expire(key, window_seconds)
    ttl = redis_connection.ttl(key)
    remaining = max(0, limit - counter)
    blocked = False
    if counter > limit:
        blocked = True
    return remaining, ttl, blocked


def check_existing_rate_limit(key, limit, detail):
    current = redis_connection.get(key)
    if current is None:
        counter = 0
    else:
        counter = int(current)
    ttl = redis_connection.ttl(key)
    if counter > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(ttl)},
        )

    return ttl, counter
