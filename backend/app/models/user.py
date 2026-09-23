from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, true, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import relationship

from app.database import Base

class UserRole(str, Enum):
    ADMIN ="ADMIN"
    USER = "USER"

class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SqlEnum(UserRole,name="user_role"),server_default="USER", nullable=False)
    is_active = Column(Boolean,nullable=False, server_default=true())
    created_at = Column(DateTime(timezone=True),nullable=False, server_default=func.now())

    reservations = relationship("ReservationModel",back_populates="user")
