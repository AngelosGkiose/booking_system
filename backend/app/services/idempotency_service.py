
from sqlalchemy.exc import IntegrityError

from fastapi import HTTPException

from starlette import status

from app.models import IdempotencyRequestModel
from app.models.idempotencyrequest import IdempotencyRequestEnum
from app.repositories.idempotency_repository import create_idempotency_request_repo, \
    get_idempotency_request_by_user_and_key



def create_idempotency_request(user_id,key,request_hash,db):
    try:
        idempotency_request = create_idempotency_request_repo(IdempotencyRequestModel(user_id=user_id,key=key,request_hash=request_hash),db)
        return idempotency_request
    except IntegrityError:
        db.rollback()
        existing_idempotency_request=get_idempotency_request_by_user_and_key(user_id,key,db)
        if existing_idempotency_request is None:
            raise
        if existing_idempotency_request.request_hash != request_hash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Idempotency key already used with different request")
        if existing_idempotency_request.status == IdempotencyRequestEnum.COMPLETED:
            if existing_idempotency_request.reservation_id is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Inconsistent idempotency state")
            return existing_idempotency_request
        elif existing_idempotency_request.status == IdempotencyRequestEnum.PROCESSING:
           raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Request with this idempotency key is already processing")
        elif existing_idempotency_request.status == IdempotencyRequestEnum.FAILED:
            if existing_idempotency_request.response_status is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Inconsistent idempotency state")
            if existing_idempotency_request.error_detail is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Inconsistent idempotency state")
            raise HTTPException(status_code=existing_idempotency_request.response_status,detail=existing_idempotency_request.error_detail)

def mark_idempotency_completed(idempotency_request,reservation_id,response_status,db):
    idempotency_request.status = IdempotencyRequestEnum.COMPLETED
    idempotency_request.reservation_id = reservation_id
    idempotency_request.response_status = response_status
    db.flush()
    return idempotency_request


def mark_idempotency_failed(idempotency_request,response_status,error_detail,db):
    idempotency_request.status = IdempotencyRequestEnum.FAILED
    idempotency_request.response_status = response_status
    idempotency_request.error_detail = error_detail
    idempotency_request.reservation_id = None
    db.flush()
    return idempotency_request