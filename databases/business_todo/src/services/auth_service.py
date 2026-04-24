from datetime import timedelta

from databases.business_todo.src.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from databases.business_todo.src.core.config import settings
from databases.business_todo.src.repositories.user_repo import UserRepository
from databases.business_todo.src.repositories.token_repo import TokenRepository
from databases.business_todo.src.utils.validators import ValidationError


class AuthService:
    """Сервис для управления аутентификацией и авторизацией"""

    @staticmethod
    def login(email: str, password: str) -> dict:
        """
        Аутентификация пользователя по email и паролю
        """
        user = UserRepository.get_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            raise ValidationError("Invalid credentials")

        if user["status"] != "active":
            raise ValidationError("User account is blocked")

        access_token = create_access_token(
            data={"sub": str(user["user_id"]), "role": user["role"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user["user_id"])},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        TokenRepository.create(user["user_id"], refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS)

        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {k: v for k, v in user.items() if k != "password_hash"}
        }

    @staticmethod
    def register(
            first_name: str,
            last_name: str,
            email: str,
            password: str,
            phone: str = None,
            role: str = "customer"
    ) -> dict:
        """
        Регистрация нового пользователя
        """
        if role not in ["customer", "executor"]:
            raise ValidationError("Invalid role for registration")

        existing = UserRepository.get_by_email(email)
        if existing:
            raise ValidationError("Email already registered", "email")

        password_hash = get_password_hash(password)
        user = UserRepository.create(first_name, last_name, email, password_hash, phone, role)

        access_token = create_access_token(
            data={"sub": str(user["user_id"]), "role": user["role"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user["user_id"])},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        TokenRepository.create(user["user_id"], refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS)

        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {k: v for k, v in user.items() if k != "password_hash"}
        }

    @staticmethod
    def logout(user_id: int) -> dict:
        """
        Выход пользователя (удаление refresh токена)
        """
        TokenRepository.delete_by_user_id(user_id)
        return {"message": "Logged out"}

    @staticmethod
    def refresh_token(refresh_token: str) -> dict:
        """
        Обновление access токена по refresh токену
        """
        if not refresh_token:
            raise ValidationError("Refresh token required")

        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValidationError("Invalid refresh token")

        stored = TokenRepository.get_by_token(refresh_token)
        if not stored:
            raise ValidationError("Refresh token not found or expired")

        user = UserRepository.get_by_id(stored["user_id"])
        if not user:
            raise ValidationError("User not found")

        new_access = create_access_token(
            data={"sub": str(user["user_id"]), "role": user["role"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "accessToken": new_access,
            "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
