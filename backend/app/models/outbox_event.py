from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class OutboxEventModel(Base):
    __tablename__ = "outbox_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    attempt_count = Column(Integer, nullable=False, server_default="0")
    last_error = Column(String, nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
