from fastapi import Depends, HTTPException
from starlette import status

from app.dependencies.get_current_user import get_current_user
from app.models import UserModel


def require_admin(current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return current_user
