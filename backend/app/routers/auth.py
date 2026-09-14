from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm


from app.dependencies.get_db import get_db
from app.schemas.auth import  TokenResponse
from app.security.jwt import create_access_token
from app.services.login import authenticate_user

router = APIRouter(prefix="/auth",tags=["auth"])

@router.post("/login",response_model=TokenResponse,status_code=status.HTTP_200_OK)
def login_user(form_data = Depends(OAuth2PasswordRequestForm),db:Session=Depends(get_db)):
     user=authenticate_user(form_data.username,form_data.password,db)
     token = create_access_token({"sub": str(user.id)})
     return {"access_token": token,"token_type": "bearer"}