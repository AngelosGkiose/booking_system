from enum import Enum

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func, UniqueConstraint
from sqlalchemy import Enum as SQLEnum

from app.database import Base


class IdempotencyRequestEnum(str, Enum):
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class IdempotencyRequestModel(Base):
    __tablename__ = "idempotency_requests"
    __table_args__ = (UniqueConstraint('user_id',"key",name="uq_user_id_key"), )
    id=Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'),nullable=False)
    key = Column(String,nullable=False)
    request_hash = Column(String,nullable=False)
    status = Column(SQLEnum(IdempotencyRequestEnum),nullable=False,server_default="PROCESSING")
    reservation_id = Column(Integer,ForeignKey('reservations.id'),nullable=True)
    response_status=Column(Integer,nullable=True)
    error_detail=Column(String,nullable=True)
    created_at = Column(DateTime(timezone=True),nullable=False,server_default=func.now())