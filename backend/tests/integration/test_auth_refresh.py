from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.models import UserModel
from app.security.jwt import create_access_token, create_refresh_token

client = TestClient(app)


def test_refresh_access_token_with_valid_refresh_token():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        refresh_token = create_refresh_token({"sub": str(user.id)})
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    finally:
        db.close()


def test_refresh_rejects_access_token():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        access_token = create_access_token({"sub": str(user.id)})
        response = client.post("/auth/refresh", json={"refresh_token": access_token})
        assert response.status_code == 401
    finally:
        db.close()


def test_refresh_rejects_expired_refresh_token():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        payload = {"sub": str(user.id), "type": "refresh", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}
        expired_refresh_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        response = client.post("/auth/refresh", json={"refresh_token": expired_refresh_token})
        assert response.status_code == 401
    finally:
        db.close()


def test_refresh_rejects_token_for_missing_user():
    db = SessionLocal()
    try:
        refresh_token = create_refresh_token({"sub": "999999"})
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 401
    finally:
        db.close()