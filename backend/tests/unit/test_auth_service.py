from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import app.services.auth_service as auth_service


def test_authenticate_user_returns_401_when_user_not_found(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        lambda email, db: None
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.authenticate_user(
            "user@example.com",
            "password123",
            db
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Incorrect email or password"


def test_authenticate_user_returns_401_when_password_is_wrong(monkeypatch):
    db = MagicMock()

    user = SimpleNamespace(
        id=1,
        email="user@example.com",
        hashed_password="hashed-password"
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        lambda email, db: user
    )

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed_password: False
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.authenticate_user(
            "user@example.com",
            "wrong-password",
            db
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Incorrect email or password"


def test_authenticate_user_returns_user_when_credentials_are_correct(monkeypatch):
    db = MagicMock()

    user = SimpleNamespace(
        id=1,
        email="user@example.com",
        hashed_password="hashed-password"
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        lambda email, db: user
    )

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed_password: True
    )

    result = auth_service.authenticate_user(
        "user@example.com",
        "correct-password",
        db
    )

    assert result is user