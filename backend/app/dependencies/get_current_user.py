

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette import status

from app.dependencies.get_db import get_db
from app.repositories.user_repository import get_user_by_id
from app.security.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
def get_current_user(token=Depends(oauth2_scheme),db: Session = Depends(get_db)):
    user_id=decode_access_token(token)
    user=get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials")
    return user