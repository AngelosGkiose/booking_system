from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.routers import health_router


def test_database_health_check_success():
    db = MagicMock()

    result = health_router.database_health_check(db)

    assert result == {"status": "ok"}
    db.execute.assert_called_once()


def test_database_health_check_database_unavailable():
    db = MagicMock()
    db.execute.side_effect = SQLAlchemyError()

    with pytest.raises(HTTPException) as exc:
        health_router.database_health_check(db)

    assert exc.value.status_code == 503
    assert exc.value.detail == "Database not available"


def test_ready_success(monkeypatch):
    db = MagicMock()

    redis_mock = MagicMock()

    monkeypatch.setattr(
        health_router,
        "redis_connection",
        redis_mock,
    )

    result = health_router.check_ready(db)

    assert result == {
        "status_database": "ok",
        "status_redis": "ok",
    }

    db.execute.assert_called_once()
    redis_mock.ping.assert_called_once()


def test_ready_returns_503_when_redis_unavailable(monkeypatch):
    db = MagicMock()

    redis_mock = MagicMock()
    redis_mock.ping.side_effect = RedisError()

    monkeypatch.setattr(
        health_router,
        "redis_connection",
        redis_mock,
    )

    with pytest.raises(HTTPException) as exc:
        health_router.check_ready(db)

    assert exc.value.status_code == 503
    assert exc.value.detail == "Redis not available"


def test_ready_returns_503_when_database_unavailable(monkeypatch):
    db = MagicMock()
    db.execute.side_effect = SQLAlchemyError()

    redis_mock = MagicMock()

    monkeypatch.setattr(
        health_router,
        "redis_connection",
        redis_mock,
    )

    with pytest.raises(HTTPException) as exc:
        health_router.check_ready(db)

    assert exc.value.status_code == 503
    assert exc.value.detail == "Database not available"


def test_redis_health_check_unavailable(monkeypatch):
    redis_mock = MagicMock()
    redis_mock.ping.side_effect = RedisError()

    monkeypatch.setattr(
        health_router,
        "redis_connection",
        redis_mock,
    )

    with pytest.raises(HTTPException) as exc:
        health_router.redis_health_check()

    assert exc.value.status_code == 503
    assert exc.value.detail == "Redis not available"


def test_redis_health_check_success(monkeypatch):
    redis_mock = MagicMock()

    monkeypatch.setattr(
        health_router,
        "redis_connection",
        redis_mock,
    )

    result = health_router.redis_health_check()

    assert result == {"status": "ok"}
    redis_mock.ping.assert_called_once()
