from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class SeatModel(Base):
    __tablename__ = 'seats'
    __table_args__ = (UniqueConstraint('venue_id',"section","row_label","seat_number",name="uq_seats_venue_section_row_number"),)
    id = Column(Integer,primary_key=True,autoincrement=True)
    venue_id = Column(Integer,ForeignKey('venues.id'),nullable=False)
    section=Column(String,nullable=False)
    row_label = Column(String,nullable=False)
    seat_number = Column(Integer,nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False,server_default=func.now())

    venue=relationship("VenueModel",back_populates="seats")