from app.models import IdempotencyRequestModel


def create_idempotency_request_repo(idempotency, db):
    db.add(idempotency)
    db.flush()
    db.refresh(idempotency)
    return idempotency


def get_idempotency_request_by_user_and_key(user_id, key, db):
    return (
        db.query(IdempotencyRequestModel)
        .filter(
            IdempotencyRequestModel.user_id == user_id,
            IdempotencyRequestModel.key == key,
        )
        .first()
    )
