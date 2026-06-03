from fastapi import APIRouter, HTTPException, status, Depends

from databases.business_todo.src.api.dependencies import get_current_user
from databases.business_todo.src.services.auth_service import AuthService
from databases.business_todo.src.utils.validators import ValidationError
from databases.business_todo.src.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Аутентификация пользователя"""
    try:
        return AuthService.login(email=request.email, password=request.password)
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={e.field: e.message} if e.field else e.message
        )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    """Регистрация нового пользователя"""
    try:
        return AuthService.register(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            password=request.password,
            phone=request.phone,
            role=request.role
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={e.field: e.message} if e.field else e.message
        )


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """Выход пользователя (удаление refresh токена)"""
    try:
        return AuthService.logout(current_user["user_id"])
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh(request: RefreshTokenRequest):
    """Обновление access токена"""
    try:
        return AuthService.refresh_token(request.refreshToken)
    except ValidationError as e:
        raise HTTPException(status_code=401, detail=e.message)
