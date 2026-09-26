from fastapi import APIRouter, Depends, HTTPException
from redis import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from app.dependencies.get_db import get_db
from app.queue import redis_connection

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    return {"status": "ok"}


@router.get("/redis")
def redis_health_check():
    try:
        redis_connection.ping()
        return {"status": "ok"}
    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis not available",
        )


@router.get("/database")
def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1")).scalar_one()
        return {"status": "ok"}
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )


@router.get("/ready")
def check_ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1")).scalar_one()
        redis_connection.ping()
        return {"status_database": "ok", "status_redis": "ok"}
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis not available",
        )
