from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class UserListParams(BaseModel):
    """Параметры фильтрации списка пользователей"""
    role: Optional[str] = Field(None, description="Фильтр по роли (customer, executor, admin)")
    status: Optional[str] = Field(None, description="Фильтр по статусу (active, blocked)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"role": "customer", "status": "active"}
            ]
        }
    }


class UserUpdate(BaseModel):
    """Запрос на обновление профиля пользователя"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Имя")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Фамилия")
    email: Optional[EmailStr] = Field(None, description="Email адрес")
    phone: Optional[str] = Field(None, max_length=20, description="Номер телефона")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "first_name": "Иван",
                    "last_name": "Иванов",
                    "email": "ivan@example.com",
                    "phone": "+79991234567"
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """Данные пользователя в ответе"""
    user_id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Список пользователей с пагинацией"""
    users: List[UserResponse]
    total: int
