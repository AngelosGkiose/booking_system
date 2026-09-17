from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_db import get_db
from app.models import UserModel
from app.schemas.auth import TokenResponse, UserResponse, RegisterRequest, RefreshTokenRequest, LogOutRequest, \
     SessionResponse
from app.security.jwt import create_access_token
from app.services.auth_service import authenticate_user, refresh_access_token_service, create_refresh_token_service, \
     logout_user_service, get_active_sessions_service, delete_user_session_service, get_user_all_sessions_service
from app.services.register import register_user_service

router = APIRouter(prefix="/auth",tags=["auth"])



@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register_user(data:RegisterRequest,db:Session = Depends(get_db),):
     return register_user_service(data.email,data.password,db)


@router.post("/login",response_model=TokenResponse,status_code=status.HTTP_200_OK)
def login_user(form_data = Depends(OAuth2PasswordRequestForm),db:Session=Depends(get_db)):
     user=authenticate_user(form_data.username,form_data.password,db)
     access_token = create_access_token({"sub": str(user.id)})
     refresh_token=create_refresh_token_service(user.id,db)
     return {"access_token":access_token,"refresh_token":refresh_token,"token_type":"bearer"}



@router.get("/me",response_model=UserResponse,status_code=status.HTTP_200_OK)
def get_me(current_user:UserModel = Depends(get_current_user),):
     return current_user


@router.post("/refresh",response_model=TokenResponse,status_code=status.HTTP_200_OK)
def refresh_access_token(data:RefreshTokenRequest,db:Session = Depends(get_db)):
     return refresh_access_token_service(data.refresh_token, db)

@router.post("/logout",status_code=status.HTTP_200_OK)
def logout_user(data:LogOutRequest,db:Session = Depends(get_db)):
      logout_user_service(data.refresh_token, db)
      return {"message": "Logged out successfully"}

@router.get("/sessions",response_model=list[SessionResponse],status_code=status.HTTP_200_OK)
def get_active_sessions(current_user:UserModel = Depends(get_current_user),db:Session = Depends(get_db)):
     return get_active_sessions_service(current_user.id,db)

@router.delete("/sessions/{session_id}",status_code=status.HTTP_200_OK)
def delete_user_session(session_id:int,current_user:UserModel=Depends(get_current_user),db:Session = Depends(get_db)):
     return delete_user_session_service(session_id,current_user.id,db)


@router.delete("/sessions",status_code=status.HTTP_204_NO_CONTENT)
def delete_all_user_sessions(current_user:UserModel=Depends(get_current_user),db:Session = Depends(get_db)):
     get_user_all_sessions_service(current_user.id,db)