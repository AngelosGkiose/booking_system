from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.reservation import ReservationStatus


class ReservationCreate(BaseModel):
    event_seat_id: int

class ReservationResponse(BaseModel):
    id:int
    user_id: int
    event_seat_id: int
    status: ReservationStatus
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)
