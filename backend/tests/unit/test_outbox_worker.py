from unittest.mock import MagicMock

import pytest

from app.workers import outbox_worker


class StopWorker(Exception):
    pass


def test_outbox_worker_processes_events_and_closes_db(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        outbox_worker,
        "SessionLocal",
        lambda: db,
    )

    process_mock = MagicMock()

    monkeypatch.setattr(
        outbox_worker,
        "publish_outbox_events_service",
        process_mock,
    )

    def stop_after_first_iteration(*args, **kwargs):
        raise StopWorker()

    monkeypatch.setattr(
        outbox_worker,
        "sleep",
        stop_after_first_iteration,
    )

    with pytest.raises(StopWorker):
        outbox_worker.run_worker()

    process_mock.assert_called_once_with(db)
    db.close.assert_called_once()
