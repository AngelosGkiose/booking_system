

from sqlalchemy import Column, Integer, String, Boolean, DateTime, true, func

from app.database import Base


class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean,nullable=False, server_default=true())
    created_at = Column(DateTime(timezone=True),nullable=False, server_default=func.now())


