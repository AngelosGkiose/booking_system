from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_db import get_db
from app.models import UserModel
from app.schemas.auth import TokenResponse, UserResponse, RegisterRequest, AccessTokenResponse, RefreshTokenRequest
from app.security.jwt import create_access_token, create_refresh_token
from app.services.auth_service import authenticate_user, refresh_access_token_service
from app.services.register import register_user_service

router = APIRouter(prefix="/auth",tags=["auth"])



@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register_user(data:RegisterRequest,db:Session = Depends(get_db),):
     return register_user_service(data.email,data.password,db)


@router.post("/login",response_model=TokenResponse,status_code=status.HTTP_200_OK)
def login_user(form_data = Depends(OAuth2PasswordRequestForm),db:Session=Depends(get_db)):
     user=authenticate_user(form_data.username,form_data.password,db)
     access_token = create_access_token({"sub": str(user.id)})
     refresh_token=create_refresh_token({"sub": str(user.id)})
     return {"access_token":access_token,"refresh_token":refresh_token,"token_type":"bearer"}



@router.get("/me",response_model=UserResponse,status_code=status.HTTP_200_OK)
def get_me(current_user:UserModel = Depends(get_current_user),):
     return current_user


@router.post("/refresh",response_model=AccessTokenResponse,status_code=status.HTTP_200_OK)
def refresh_access_token(data:RefreshTokenRequest,db:Session = Depends(get_db)):
     return refresh_access_token_service(data.refresh_token, db)