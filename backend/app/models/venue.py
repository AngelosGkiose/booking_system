from sqlalchemy import Column, Integer, String, DateTime, func

from app.database import Base


class VenueModel(Base):
    __tablename__ = 'venues'
    id = Column(Integer, primary_key=True,autoincrement=True)
    name = Column(String,nullable=False)
    address = Column(String,nullable=False)
    city = Column(String,nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False,server_default=func.now())
