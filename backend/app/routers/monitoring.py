from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.dependencies.get_db import get_db
from app.dependencies.require_admin import require_admin
from app.models import UserModel
from app.schemas.monitoring import MonitoringOutboxEvents
from app.services.monitoring_service import monitoring_outbox_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get(
    "/outbox", response_model=MonitoringOutboxEvents, status_code=status.HTTP_200_OK
)
def monitoring_outbox(
    current_user: UserModel = Depends(require_admin), db: Session = Depends(get_db)
):
    return monitoring_outbox_service(db)
