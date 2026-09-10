from datetime import datetime, timedelta
from enum import Enum
from zoneinfo import ZoneInfo

from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base


class ReservationStatus(str,Enum):
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    EXPIRED = 'EXPIRED'
    CANCELED = 'CANCELED'

class ReservationModel(Base):
    __tablename__="reservations"
    id=Column(Integer,primary_key=True,autoincrement=True)
    user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
    event_seat_id = Column(Integer,ForeignKey("event_seats.id"),nullable=False)
    status = Column(SQLEnum(ReservationStatus,name="reservation_status"),nullable=False,default=ReservationStatus.PENDING)
    created_at = Column(DateTime(timezone=True),nullable=False,server_default=func.now())
    expires_at = Column(DateTime(timezone=True),nullable=False,default=lambda:datetime.now(ZoneInfo("Europe/Athens")) + timedelta(minutes=10))

    user = relationship("UserModel",back_populates="reservations")
    event_seat = relationship("EventSeatModel",back_populates="reservations")