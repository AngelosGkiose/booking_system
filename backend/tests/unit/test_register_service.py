from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services import register


def test_register_user_success(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        register,
        "get_user_by_email",
        lambda email, db: None,
    )

    monkeypatch.setattr(
        register,
        "hash_password",
        lambda password: "hashed_password",
    )

    added_users = []

    def fake_add_user(user, db):
        added_users.append(user)

    monkeypatch.setattr(register, "add_user", fake_add_user)

    register.register_user_service(
        "user@test.com",
        "password123",
        db,
    )

    assert len(added_users) == 1
    assert added_users[0].email == "user@test.com"
    assert added_users[0].hashed_password == "hashed_password"

    db.commit.assert_called_once()


def test_register_user_rejects_existing_email(monkeypatch):
    db = MagicMock()

    existing_user = MagicMock()

    monkeypatch.setattr(
        register,
        "get_user_by_email",
        lambda email, db: existing_user,
    )

    with pytest.raises(HTTPException) as exc:
        register.register_user_service(
            "user@test.com",
            "password123",
            db,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "Email already registered"

    db.rollback.assert_called_once()


def test_register_user_rolls_back_when_commit_fails(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        register,
        "get_user_by_email",
        lambda email, db: None,
    )

    monkeypatch.setattr(
        register,
        "hash_password",
        lambda password: "hashed_password",
    )

    monkeypatch.setattr(
        register,
        "add_user",
        lambda user, db: None,
    )

    db.commit.side_effect = RuntimeError("Commit failed")

    with pytest.raises(RuntimeError, match="Commit failed"):
        register.register_user_service(
            "user@test.com",
            "password123",
            db,
        )

    db.rollback.assert_called_once()
