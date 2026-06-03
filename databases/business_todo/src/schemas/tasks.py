from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from fastapi import Query


class TaskCreate(BaseModel):
    task_text: str = Field(..., min_length=1, max_length=200, description="Текст задачи")
    description: Optional[str] = Field(None, max_length=2000, description="Описание")
    priority: str = Field(default="medium", pattern="^(low|medium|high)$", description="Приоритет")
    deadline: Optional[datetime] = Field(None, description="Дедлайн")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_text": "Найти кота",
                    "description": "Рыжий, отзывается на Мурзик",
                    "priority": "high",
                    "deadline": "2025-01-15T18:00:00"
                }
            ]
        }
    }


class TaskUpdate(BaseModel):
    task_text: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    deadline: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(new|in_progress|completed|cancelled)$")
    executor_id: Optional[int] = None


class TaskResponse(BaseModel):
    task_id: int
    task_text: str
    description: Optional[str]
    customer_id: int
    executor_id: Optional[int]
    status: str
    priority: str
    deadline: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
    page: int
    limit: int


# Обратите внимание на код ниже: все запросы Query
# То есть в Postman надо будет прям конкретно вбивать в адрес, к которому обращаетесь, а не в body
# Для примера:
# /api/v1/tasks?page=1&limit=20 - GET запрос
class TaskListRequest(BaseModel):
    status_filter: Optional[str] = Query(None, alias="status", description="Фильтр по статусу")
    priority: Optional[str] = Query(None, description="Фильтр по приоритету")
    customer_id: Optional[str] = Query(None, description="ID заказчика или 'me'")
    executor_id: Optional[str] = Query(None, description="ID исполнителя или 'me'")
    page: int = Query(1, ge=1, description="Номер страницы")
    limit: int = Query(20, ge=1, le=100, description="Количество записей")


class ClaimTaskResponse(BaseModel):
    """Ответ после взятия задачи в работу"""
    task_id: int
    task_text: str
    status: str
    executor_id: int
    priority: str
    deadline: Optional[datetime]
    updated_at: datetime

    model_config = {"from_attributes": True}
