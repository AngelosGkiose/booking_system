from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime, UniqueConstraint
from sqlalchemy  import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base



class EventSeatStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    RESERVED = "RESERVED"


class EventSeatModel(Base):
    __tablename__ = "event_seats"
    __table_args__ = (UniqueConstraint('event_id', 'seat_id', name='uq_event_seats'),)
    id = Column(Integer, primary_key=True,autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id'),nullable=False)
    seat_id = Column(Integer, ForeignKey('seats.id'),nullable=False)
    status =Column(SQLEnum(EventSeatStatus, name="event_seat_status"),nullable=False,default=EventSeatStatus.AVAILABLE)
    price = Column(Numeric(10, 2),nullable=False)
    hold_expires_at = Column(DateTime(timezone=True),nullable=True)

    event=relationship("EventModel",back_populates="event_seats")
    seat=relationship("SeatModel",back_populates="event_seats")

