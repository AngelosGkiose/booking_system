from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String

from app.config import settings
from app.database import Base


class RefreshTokenModel(Base):
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'),nullable=False)
    jti = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expiration_days),nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc),nullable=False)