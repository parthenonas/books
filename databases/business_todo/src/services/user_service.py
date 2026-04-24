from typing import Optional, List
from databases.business_todo.src.repositories.user_repo import UserRepository
from databases.business_todo.src.utils.validators import ValidationError


class UserService:
    """Сервис для управления пользователями"""

    @staticmethod
    def get_me(user_id: int) -> dict:
        """Получить данные текущего пользователя"""
        user = UserRepository.get_by_id(user_id)
        if not user:
            raise ValidationError("User not found")

        return {k: v for k, v in user.items() if k != "password_hash"}

    @staticmethod
    def get_users(
            role: Optional[str] = None,
            status: Optional[str] = None,
            current_user: Optional[dict] = None
    ) -> dict:
        """Получить список пользователей (только admin)"""
        if current_user["role"] != "admin":
            raise ValidationError("Not enough permissions")

        users = UserRepository.get_all(role=role, status=status)
        users = [{k: v for k, v in u.items() if k != "password_hash"} for u in users]

        return {
            "users": users,
            "total": len(users)
        }

    @staticmethod
    def update_user(user_id: int, update_data: dict, current_user: dict) -> dict:
        if current_user["role"] != "admin" and current_user["user_id"] != user_id:
            raise ValidationError("Not enough permissions")

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise ValidationError("User not found")

        if "email" in update_data and update_data["email"]:
            existing = UserRepository.get_by_email(update_data["email"])
            if existing and existing["user_id"] != user_id:
                raise ValidationError("Email already registered", "email")

        return UserRepository.update(user_id, **update_data)
