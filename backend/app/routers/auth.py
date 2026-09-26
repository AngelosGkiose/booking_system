from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_db import get_db
from app.models import UserModel
from app.schemas.auth import (
    LogOutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    SessionResponse,
    TokenResponse,
    UserResponse,
)
from app.security.jwt import create_access_token
from app.services.auth_service import (
    authenticate_user,
    create_refresh_token_service,
    delete_user_session_service,
    get_active_sessions_service,
    get_user_all_sessions_service,
    logout_user_service,
    refresh_access_token_service,
)
from app.services.rate_limit_service import (
    check_existing_rate_limit,
    clear_rate_limit,
    record_rate_limit_attempt,
)
from app.services.register import register_user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register_user(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    return register_user_service(data.email, data.password, db)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_user(
    request: Request,
    form_data=Depends(OAuth2PasswordRequestForm),
    db: Session = Depends(get_db),
):
    client = request.client
    if client is None:
        client_ip = "unknown"
        key = f"rate_limit:login:ip:{client_ip}"
    else:
        client_ip = client.host
        key = f"rate_limit:login:ip:{client_ip}"
    email_key = f"rate_limit:login:email:{form_data.username.lower()}"
    check_existing_rate_limit(key, 5, "Too many login requests")
    check_existing_rate_limit(email_key, 5, "Too many login requests")
    try:
        user = authenticate_user(form_data.username, form_data.password, db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            ip_remaining, ip_ttl, ip_blocked = record_rate_limit_attempt(key, 5, 60)
            email_remaining, email_ttl, email_blocked = record_rate_limit_attempt(
                email_key, 5, 300
            )
            if ip_blocked:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login requests",
                    headers={
                        "Retry-After": str(ip_ttl),
                        "X-RateLimit-Limit": "5",
                        "X-RateLimit-Remaining": str(ip_remaining),
                        "X-RateLimit-Reset": str(ip_ttl),
                    },
                )
            elif email_blocked:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login requests",
                    headers={
                        "Retry-After": str(email_ttl),
                        "X-RateLimit-Limit": "5",
                        "X-RateLimit-Remaining": str(email_remaining),
                        "X-RateLimit-Reset": str(email_ttl),
                    },
                )
        raise
    clear_rate_limit(key)
    clear_rate_limit(email_key)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token_service(user.id, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(
    current_user: UserModel = Depends(get_current_user),
):
    return current_user


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh_access_token(
    request: Request,
    response: Response,
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    client = request.client
    if client is None:
        client_ip = "unknown"
        key = f"rate_limit:refresh:ip:{client_ip}"
    else:
        client_ip = client.host
        key = f"rate_limit:refresh:ip:{client_ip}"
    remaining, ttl, blocked = record_rate_limit_attempt(key, 20, 60)
    if blocked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many refresh requests",
            headers={
                "Retry-After": str(ttl),
                "X-RateLimit-Limit": "20",
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(ttl),
            },
        )
    response.headers["X-RateLimit-Limit"] = "20"
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(ttl)
    return refresh_access_token_service(data.refresh_token, db)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(data: LogOutRequest, db: Session = Depends(get_db)):
    logout_user_service(data.refresh_token, db)
    return {"message": "Logged out successfully"}


@router.get(
    "/sessions", response_model=list[SessionResponse], status_code=status.HTTP_200_OK
)
def get_active_sessions(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    return get_active_sessions_service(current_user.id, db)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def delete_user_session(
    session_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_user_session_service(session_id, current_user.id, db)


@router.delete("/sessions", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_user_sessions(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_user_all_sessions_service(current_user.id, db)
