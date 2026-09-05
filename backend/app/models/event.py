from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class EventModel(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True,autoincrement=True)
    __table_args__ = (UniqueConstraint("venue_id","name","start_time",name="uq_event_venue_name_start"),
                          CheckConstraint("end_time>start_time",name="ck_event_end_after_start"))
    venue_id = Column(Integer,ForeignKey('venues.id'),nullable=False)
    name = Column(String,nullable=False)
    start_time = Column(DateTime(timezone=True),nullable=False)
    end_time = Column(DateTime(timezone=True),nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False,server_default=func.now())

    venue=relationship("VenueModel",back_populates="events")
