from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_db import get_db
from app.models import UserModel
from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.services.reservation_service import create_reservation_service

router = APIRouter(prefix="/reservations", tags=["reservations"])

@router.post("/create",response_model=ReservationResponse,status_code=status.HTTP_201_CREATED)
def create_reservation(reservation_data: ReservationCreate,current_user:UserModel = Depends(get_current_user),db: Session = Depends(get_db)):
    return create_reservation_service(reservation_data.event_seat_id,db,current_user)