from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services import auth_service


def test_authenticate_user_returns_401_when_user_not_found(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(auth_service, "get_user_by_email", lambda email, db: None)

    with pytest.raises(HTTPException) as exc:
        auth_service.authenticate_user("user@example.com", "password123", db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Incorrect email or password"


def test_authenticate_user_returns_401_when_password_is_wrong(monkeypatch):
    db = MagicMock()

    user = SimpleNamespace(
        id=1, email="user@example.com", hashed_password="hashed-password"
    )

    monkeypatch.setattr(auth_service, "get_user_by_email", lambda email, db: user)

    monkeypatch.setattr(
        auth_service, "verify_password", lambda password, hashed_password: False
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.authenticate_user("user@example.com", "wrong-password", db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Incorrect email or password"


def test_authenticate_user_returns_user_when_credentials_are_correct(monkeypatch):
    db = MagicMock()

    user = SimpleNamespace(
        id=1, email="user@example.com", hashed_password="hashed-password"
    )

    monkeypatch.setattr(auth_service, "get_user_by_email", lambda email, db: user)

    monkeypatch.setattr(
        auth_service, "verify_password", lambda password, hashed_password: True
    )

    result = auth_service.authenticate_user("user@example.com", "correct-password", db)

    assert result is user


def test_refresh_rejects_missing_refresh_token_record(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: (1, "jti-123"),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_refresh_token_for_update",
        lambda user_id, jti, db: None,
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_id",
        lambda user_id, db: SimpleNamespace(id=1),
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.refresh_access_token_service("token", db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Could not validate refresh token"


def test_refresh_rejects_missing_user(monkeypatch):
    db = MagicMock()

    token_record = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: (1, "jti-123"),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_refresh_token_for_update",
        lambda user_id, jti, db: token_record,
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_id",
        lambda user_id, db: None,
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.refresh_access_token_service("token", db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Could not validate credentials"


def test_refresh_rejects_revoked_token(monkeypatch):
    db = MagicMock()

    token_record = SimpleNamespace(
        revoked_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: (1, "jti-123"),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_refresh_token_for_update",
        lambda user_id, jti, db: token_record,
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_id",
        lambda user_id, db: SimpleNamespace(id=1),
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.refresh_access_token_service("token", db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Refresh token has been revoked"


def test_refresh_rejects_expired_token(monkeypatch):
    db = MagicMock()

    token_record = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: (1, "jti-123"),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_refresh_token_for_update",
        lambda user_id, jti, db: token_record,
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_id",
        lambda user_id, db: SimpleNamespace(id=1),
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.refresh_access_token_service("token", db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Refresh token has expired"


def test_refresh_success_rotates_token(monkeypatch):
    db = MagicMock()

    token_record = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    user = SimpleNamespace(id=1)

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: (1, "jti-123"),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_refresh_token_for_update",
        lambda user_id, jti, db: token_record,
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_id",
        lambda user_id, db: user,
    )

    monkeypatch.setattr(
        auth_service,
        "create_refresh_token_service",
        lambda user_id, db, commit=False: "new-refresh-token",
    )

    monkeypatch.setattr(
        auth_service,
        "create_access_token",
        lambda data: "new-access-token",
    )

    result = auth_service.refresh_access_token_service("old-token", db)

    assert result == {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }

    assert token_record.revoked_at is not None
    db.commit.assert_called_once()


def test_refresh_rolls_back_when_commit_fails(monkeypatch):
    db = MagicMock()

    token_record = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: (1, "jti-123"),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_refresh_token_for_update",
        lambda user_id, jti, db: token_record,
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_id",
        lambda user_id, db: SimpleNamespace(id=1),
    )

    monkeypatch.setattr(
        auth_service,
        "create_refresh_token_service",
        lambda user_id, db, commit=False: "new-refresh-token",
    )

    monkeypatch.setattr(
        auth_service,
        "create_access_token",
        lambda data: "new-access-token",
    )

    db.commit.side_effect = RuntimeError("Commit failed")

    with pytest.raises(RuntimeError, match="Commit failed"):
        auth_service.refresh_access_token_service("token", db)

    db.rollback.assert_called_once()


def test_create_refresh_token_service_success(monkeypatch):
    db = MagicMock()

    added_tokens = []

    monkeypatch.setattr(
        auth_service,
        "create_refresh_token",
        lambda data, jti, exp_time: "refresh-token",
    )

    monkeypatch.setattr(
        auth_service,
        "add_refresh_token",
        lambda token_model, db: added_tokens.append(token_model),
    )

    result = auth_service.create_refresh_token_service(1, db)

    assert result == "refresh-token"
    assert len(added_tokens) == 1
    assert added_tokens[0].user_id == 1

    db.commit.assert_called_once()


def test_create_refresh_token_service_rolls_back_when_commit_fails(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        auth_service,
        "create_refresh_token",
        lambda data, jti, exp_time: "refresh-token",
    )

    monkeypatch.setattr(
        auth_service,
        "add_refresh_token",
        lambda token_model, db: None,
    )

    db.commit.side_effect = RuntimeError("Commit failed")

    with pytest.raises(RuntimeError, match="Commit failed"):
        auth_service.create_refresh_token_service(1, db)

    db.rollback.assert_called_once()


def test_logout_rejects_missing_user(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: (1, "jti"),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_id",
        lambda user_id, db: None,
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_refresh_token",
        lambda user_id, jti, db: MagicMock(),
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.logout_user_service("token", db)

    assert exc.value.status_code == 401


def test_logout_returns_when_token_already_revoked(monkeypatch):
    db = MagicMock()

    token_record = SimpleNamespace(
        revoked_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: (1, "jti"),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_id",
        lambda user_id, db: SimpleNamespace(id=1),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_refresh_token",
        lambda user_id, jti, db: token_record,
    )

    result = auth_service.logout_user_service("token", db)

    assert result is None
    db.commit.assert_not_called()


def test_logout_success_revokes_token(monkeypatch):
    db = MagicMock()

    token_record = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: (1, "jti"),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_by_id",
        lambda user_id, db: SimpleNamespace(id=1),
    )

    monkeypatch.setattr(
        auth_service,
        "get_user_refresh_token",
        lambda user_id, jti, db: token_record,
    )

    auth_service.logout_user_service("token", db)

    assert token_record.revoked_at is not None
    db.commit.assert_called_once()
