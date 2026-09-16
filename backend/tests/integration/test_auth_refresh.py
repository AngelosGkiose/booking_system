from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.models import UserModel
from app.repositories.refresh_token_repository import get_user_refresh_token
from app.security.jwt import create_access_token, create_refresh_token, decode_refresh_token
from app.services.auth_service import create_refresh_token_service

client = TestClient(app)


def test_refresh_access_token_with_valid_refresh_token():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        refresh_token = create_refresh_token_service(user.id, db)
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
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
        payload = {"sub": str(user.id), "type": "refresh", "jti": str(uuid4()), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}
        expired_refresh_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        response = client.post("/auth/refresh", json={"refresh_token": expired_refresh_token})
        assert response.status_code == 401
    finally:
        db.close()


def test_refresh_rejects_token_for_missing_user():
    db = SessionLocal()
    try:
        jti = str(uuid4())
        exp_time = datetime.now(timezone.utc) + timedelta(days=1)
        refresh_token = create_refresh_token({"sub": "999999"}, jti, exp_time)
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 401
    finally:
        db.close()


def test_refresh_token_rotation_revokes_old_token():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        old_refresh_token = create_refresh_token_service(user.id, db)
        response_1 = client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
        assert response_1.status_code == 200
        data = response_1.json()
        new_refresh_token = data["refresh_token"]
        assert new_refresh_token != old_refresh_token
        response_2 = client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
        assert response_2.status_code == 401
    finally:
        db.close()

def test_new_refresh_token_can_be_used():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        old_refresh_token = create_refresh_token_service(user.id, db)
        response_1 = client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
        assert response_1.status_code == 200
        new_refresh_token = response_1.json()["refresh_token"]
        response_2 = client.post("/auth/refresh", json={"refresh_token": new_refresh_token})
        assert response_2.status_code == 200
        assert "access_token" in response_2.json()
        assert "refresh_token" in response_2.json()
    finally:
        db.close()

def test_rotation_sets_revoked_at_on_old_token():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        old_refresh_token = create_refresh_token_service(user.id, db)
        user_id, old_jti = decode_refresh_token(old_refresh_token)
        response = client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
        assert response.status_code == 200
        db.expire_all()
        old_token_record = get_user_refresh_token(user_id, old_jti, db)
        assert old_token_record is not None
        assert old_token_record.revoked_at is not None
    finally:
        db.close()

def test_refresh_rejects_token_without_jti():
    db = SessionLocal()
    try:
        user = UserModel(email="user@test.com", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
        payload = {"sub": str(user.id), "type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(days=1)}
        refresh_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 401
    finally:
        db.close()