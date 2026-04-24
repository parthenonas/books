from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "secure123"
                }
            ]
        }
    }


class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="Имя")
    last_name: str = Field(..., min_length=1, max_length=50, description="Фамилия")
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50, description="Пароль")
    phone: Optional[str] = Field(None, max_length=20, description="Телефон")
    role: str = Field(default="customer", pattern="^(customer|executor)$", description="Роль")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "first_name": "Иван",
                    "last_name": "Иванов",
                    "email": "ivan@example.com",
                    "password": "secure123",
                    "phone": "+79991234567",
                    "role": "customer"
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    user: dict

    model_config = {"from_attributes": True}


class RefreshTokenRequest(BaseModel):
    refreshToken: str


class RefreshTokenResponse(BaseModel):
    accessToken: str
    expiresIn: int


class UserResponse(BaseModel):
    user_id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
