from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict,field_validator


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one number")

        if not any(not char.isalnum() for char in password):
            raise ValueError("Password must contain at least one special character")

        return password



class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str