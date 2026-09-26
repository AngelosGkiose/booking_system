from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app.services.outbox_event_service as outbox_service

FIXED_NOW = datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED_NOW


@pytest.mark.parametrize(
    "starting_attempts, expected_attempts, expected_delay",
    [
        (0, 1, 10),
        (1, 2, 30),
        (2, 3, 60),
        (3, 4, 300),
    ],
)
def test_failed_attempt_schedules_retry(
    monkeypatch,
    starting_attempts,
    expected_attempts,
    expected_delay,
):
    monkeypatch.setattr(outbox_service, "datetime", FixedDateTime)

    event = SimpleNamespace(
        id=1,
        attempt_count=starting_attempts,
        last_error=None,
        failed_at=None,
        next_attempt_at=None,
    )

    db = MagicMock()

    result = outbox_service.mark_outbox_event_failed_attempt(
        event,
        "Redis unavailable",
        max_attempts=10,
        db=db,
    )

    assert result is event
    assert event.attempt_count == expected_attempts
    assert event.last_error == "Redis unavailable"
    assert event.failed_at is None
    assert event.next_attempt_at == FIXED_NOW + timedelta(seconds=expected_delay)

    db.flush.assert_called_once_with()


def test_failed_attempt_marks_event_permanently_failed(monkeypatch):
    monkeypatch.setattr(outbox_service, "datetime", FixedDateTime)

    event = SimpleNamespace(
        id=1,
        attempt_count=9,
        last_error=None,
        failed_at=None,
        next_attempt_at=FIXED_NOW + timedelta(seconds=300),
    )

    db = MagicMock()

    result = outbox_service.mark_outbox_event_failed_attempt(
        event,
        "Redis unavailable",
        max_attempts=10,
        db=db,
    )

    assert result is event
    assert event.attempt_count == 10
    assert event.last_error == "Redis unavailable"
    assert event.failed_at == FIXED_NOW
    assert event.next_attempt_at is None

    db.flush.assert_called_once_with()


def test_publish_outbox_events_processes_each_candidate(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        outbox_service,
        "get_unprocessed_outbox_event_ids_repo",
        lambda db: [10, 20, 30],
    )

    processed_ids = []

    monkeypatch.setattr(
        outbox_service,
        "process_one_outbox_event",
        lambda event_id: processed_ids.append(event_id),
    )

    outbox_service.publish_outbox_events_service(db)

    assert processed_ids == [10, 20, 30]


def test_process_one_outbox_event_returns_when_event_not_found(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        outbox_service,
        "SessionLocal",
        lambda: db,
    )

    monkeypatch.setattr(
        outbox_service,
        "get_outbox_event_for_update_repo",
        lambda event_id, db: None,
    )

    outbox_service.process_one_outbox_event(123)

    db.close.assert_called_once()
