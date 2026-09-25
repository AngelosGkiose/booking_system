from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import app.services.reservation_service as reservation_service


def test_get_user_reservations_rejects_invalid_date_range():
    db = MagicMock()
    current_user = SimpleNamespace(id=1)

    date_from = datetime(2026, 9, 20)
    date_to = datetime(2026, 9, 10)

    with pytest.raises(HTTPException) as exc:
        reservation_service.get_user_reservations_service(
            sort_by="created_at",
            order="asc",
            event_id=None,
            reservation_status=None,
            date_from=date_from,
            date_to=date_to,
            page=1,
            limit=10,
            current_user=current_user,
            db=db
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "date_from must be before date_to"


def test_get_user_reservations_rejects_invalid_sort_by():
    db = MagicMock()
    current_user = SimpleNamespace(id=1)

    with pytest.raises(HTTPException) as exc:
        reservation_service.get_user_reservations_service(
            sort_by="price",
            order="asc",
            event_id=None,
            reservation_status=None,
            date_from=None,
            date_to=None,
            page=1,
            limit=10,
            current_user=current_user,
            db=db
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort_by value"


def test_get_user_reservations_rejects_invalid_order():
    db = MagicMock()
    current_user = SimpleNamespace(id=1)

    with pytest.raises(HTTPException) as exc:
        reservation_service.get_user_reservations_service(
            sort_by="created_at",
            order="random",
            event_id=None,
            reservation_status=None,
            date_from=None,
            date_to=None,
            page=1,
            limit=10,
            current_user=current_user,
            db=db
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid order value"


def test_get_user_reservations_returns_correct_pagination(monkeypatch):
    db = MagicMock()
    current_user = SimpleNamespace(id=5)

    reservations = [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2)
    ]

    monkeypatch.setattr(
        reservation_service,
        "count_user_reservations_repo",
        lambda *args, **kwargs: 25
    )

    monkeypatch.setattr(
        reservation_service,
        "get_user_reservations_repo",
        lambda *args, **kwargs: reservations
    )

    result = reservation_service.get_user_reservations_service(
        sort_by="created_at",
        order="desc",
        event_id=None,
        reservation_status=None,
        date_from=None,
        date_to=None,
        page=2,
        limit=10,
        current_user=current_user,
        db=db
    )

    assert result["items"] == reservations
    assert result["total_items"] == 25
    assert result["page"] == 2
    assert result["limit"] == 10
    assert result["total_pages"] == 3
    assert result["has_next"] is True
    assert result["has_previous"] is True