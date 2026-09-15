from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_db import get_db
from app.models import UserModel
from app.models.reservation import ReservationStatus
from app.schemas.reservation import ReservationCreate, ReservationResponse, ReservationPage
from app.services.reservation_service import create_reservation_service, confirm_reservation_service, \
    cancel_reservation_service, get_user_reservations_service, get_user_reservation_by_id_service

router = APIRouter(prefix="/reservations", tags=["reservations"])

@router.post("/create",response_model=ReservationResponse,status_code=status.HTTP_201_CREATED)
def create_reservation(reservation_data: ReservationCreate,current_user:UserModel = Depends(get_current_user),db: Session = Depends(get_db)):
    return create_reservation_service(reservation_data.event_seat_id,db,current_user)


@router.post("/{reservation_id}/confirm",response_model=ReservationResponse,status_code=status.HTTP_200_OK)
def confirm_reservation(reservation_id: int,current_user:UserModel = Depends(get_current_user),db: Session = Depends(get_db)):
    return confirm_reservation_service(reservation_id,db,current_user)

@router.post("/{reservation_id}/cancel",response_model=ReservationResponse,status_code=status.HTTP_200_OK)
def cancel_reservation(reservation_id: int,current_user:UserModel = Depends(get_current_user),db: Session = Depends(get_db)):
    return cancel_reservation_service(reservation_id,db,current_user)


@router.get("/",response_model=ReservationPage,status_code=status.HTTP_200_OK)
def get_reservations(sort_by: str = Query(default="created_at"),order: str = Query(default="desc"),event_id:int | None = Query(default=None, gt=0),reservation_status: ReservationStatus | None = Query(default=None),date_from:date| None = Query(default=None),date_to:date| None = Query(default=None),page:int=Query(default=1,ge=1),limit:int=Query(default=20,gt=0,le=100),current_user:UserModel = Depends(get_current_user),db: Session = Depends(get_db)):
    return get_user_reservations_service(sort_by,order,event_id,reservation_status,date_from,date_to,page,limit,current_user,db)


@router.get("/{reservation_id}",response_model=ReservationResponse,status_code=status.HTTP_200_OK)
def get_reservation_by_id(reservation_id: int,current_user:UserModel = Depends(get_current_user),db: Session = Depends(get_db)):
    return get_user_reservation_by_id_service(reservation_id, db, current_user)