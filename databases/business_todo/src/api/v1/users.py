from fastapi import APIRouter, Depends, HTTPException

from databases.business_todo.src.services.user_service import UserService
from databases.business_todo.src.utils.validators import ValidationError
from databases.business_todo.src.api.dependencies import get_current_user
from databases.business_todo.src.schemas.users import (
    UserListParams,
    UserUpdate,
    UserResponse,
    UserListResponse
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, summary="Получить мой профиль")
def get_me(current_user: dict = Depends(get_current_user)):
    """Получить данные текущего авторизованного пользователя"""
    try:
        return UserService.get_me(current_user["user_id"])
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("", response_model=UserListResponse, summary="Получить список пользователей")
def get_users(
        params: UserListParams = Depends(),
        current_user: dict = Depends(get_current_user)
):
    """
    Получить список всех пользователей (только для admin)

    - **role**: Фильтр по роли (customer, executor, admin)
    - **status**: Фильтр по статусу (active, blocked)
    """
    try:
        return UserService.get_users(
            role=params.role,
            status=params.status,
            current_user=current_user
        )
    except ValidationError as e:
        status_code = 403 if "permission" in e.message.lower() else 400
        raise HTTPException(status_code=status_code, detail=e.message)


@router.put("/{user_id}", response_model=UserResponse, summary="Обновить профиль пользователя")
def update_user(
        user_id: int,
        request: UserUpdate,
        current_user: dict = Depends(get_current_user)
):
    print(user_id)
    """
    Обновить данные пользователя

    - **user_id**: ID пользователя в пути (нельзя изменить)
    - **request**: Данные для обновления (только указанные поля)

    Права доступа:
    - Пользователь может обновить только свой профиль
    - Admin может обновить любой профиль

    **user_id из пути используется для обновления, игнорируя любой user_id в теле запроса**
    """
    try:
        return UserService.update_user(
            user_id,
            request.model_dump(exclude_unset=True),
            current_user
        )
    except ValidationError as e:
        if "not found" in e.message.lower():
            status_code = 404
        elif "permission" in e.message.lower():
            status_code = 403
        else:
            status_code = 400
        raise HTTPException(
            status_code=status_code,
            detail={e.field: e.message} if e.field else e.message
        )