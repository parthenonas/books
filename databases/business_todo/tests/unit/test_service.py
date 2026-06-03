import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from databases.business_todo.src.services.task_service import TaskService
from databases.business_todo.src.services.auth_service import AuthService
from databases.business_todo.src.services.user_service import UserService
from databases.business_todo.src.utils.validators import ValidationError


class TestTaskService:
    """Тесты для TaskService"""

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_create_task_success(self, mock_repo):
        """Customer успешно создаёт задачу"""
        mock_repo.create.return_value = {
            "task_id": 1,
            "task_text": "Test task",
            "description": "Desc",
            "priority": "low",
            "status": "new",
            "customer_id": 1,
            "executor_id": None,
            "deadline": None,
            "completed_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        current_user = {"user_id": 1, "role": "customer"}

        result = TaskService.create_task(
            task_text="Test task",
            description="Desc",
            priority="low",
            deadline=None,
            current_user=current_user
        )

        assert result["task_id"] == 1
        assert result["status"] == "new"
        mock_repo.create.assert_called_once()

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_create_task_wrong_role(self, mock_repo):
        """Executor не может создавать задачи"""
        current_user = {"user_id": 2, "role": "executor"}

        with pytest.raises(ValidationError, match="Not enough permissions"):
            TaskService.create_task(
                task_text="Test",
                priority="low",
                current_user=current_user
            )

        mock_repo.create.assert_not_called()

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_create_task_admin_success(self, mock_repo):
        """Admin тоже может создавать задачи"""
        mock_repo.create.return_value = {"task_id": 1, "status": "new"}

        current_user = {"user_id": 3, "role": "admin"}

        result = TaskService.create_task(
            task_text="Admin task",
            priority="high",
            current_user=current_user
        )

        assert result["status"] == "new"
        mock_repo.create.assert_called_once()

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_get_task_success(self, mock_repo):
        """Успешное получение задачи"""
        mock_repo.get_by_id.return_value = {
            "task_id": 1,
            "task_text": "Test",
            "customer_id": 1,
            "executor_id": None,
            "status": "new",
            "priority": "medium"
        }

        current_user = {"user_id": 1, "role": "customer"}

        result = TaskService.get_task(1, current_user)

        assert result["task_id"] == 1
        mock_repo.get_by_id.assert_called_once_with(1)

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_get_task_not_found(self, mock_repo):
        """Задача не найдена"""
        mock_repo.get_by_id.return_value = None

        current_user = {"user_id": 1, "role": "customer"}

        with pytest.raises(ValidationError, match="Task not found"):
            TaskService.get_task(999, current_user)

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_get_task_executor_permission(self, mock_repo):
        """Executor видит только свои задачи"""
        mock_repo.get_by_id.return_value = {
            "task_id": 1,
            "task_text": "Test",
            "customer_id": 5,
            "executor_id": 10,
            "status": "in_progress"
        }

        current_user = {"user_id": 2, "role": "executor"}

        with pytest.raises(ValidationError, match="Not enough permissions"):
            TaskService.get_task(1, current_user)

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_get_task_executor_own_task(self, mock_repo):
        """Executor видит свою задачу"""
        mock_repo.get_by_id.return_value = {
            "task_id": 1,
            "task_text": "My task",
            "customer_id": 5,
            "executor_id": 2,
            "status": "in_progress"
        }

        current_user = {"user_id": 2, "role": "executor"}

        result = TaskService.get_task(1, current_user)

        assert result["task_text"] == "My task"

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_update_task_customer_success(self, mock_repo):
        """Customer обновляет свою задачу"""
        mock_repo.get_by_id.return_value = {
            "task_id": 1,
            "customer_id": 1,
            "status": "new"
        }
        mock_repo.update.return_value = {
            "task_id": 1,
            "customer_id": 1,
            "status": "new",
            "priority": "high"
        }

        current_user = {"user_id": 1, "role": "customer"}
        update_data = {"priority": "high"}

        result = TaskService.update_task(1, update_data, current_user)

        assert result["priority"] == "high"
        mock_repo.update.assert_called_once()

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_update_task_customer_other_task(self, mock_repo):
        """Customer не может обновить чужую задачу"""
        mock_repo.get_by_id.return_value = {
            "task_id": 1,
            "customer_id": 5,
            "status": "new"
        }

        current_user = {"user_id": 1, "role": "customer"}

        with pytest.raises(ValidationError, match="Not your task"):
            TaskService.update_task(1, {"priority": "high"}, current_user)

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_update_task_executor_status_only(self, mock_repo):
        """Executor может менять только status"""
        mock_repo.get_by_id.return_value = {
            "task_id": 1,
            "executor_id": 2,
            "status": "in_progress"
        }
        mock_repo.update.return_value = {"task_id": 1, "status": "completed"}

        current_user = {"user_id": 2, "role": "executor"}

        result = TaskService.update_task(1, {"status": "completed"}, current_user)
        assert result["status"] == "completed"

        with pytest.raises(ValidationError, match="Cannot update priority"):
            TaskService.update_task(1, {"priority": "high"}, current_user)

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_update_task_admin_full_access(self, mock_repo):
        """Admin может обновлять любые поля"""
        mock_repo.get_by_id.return_value = {"task_id": 1, "customer_id": 5}
        mock_repo.update.return_value = {"task_id": 1, "priority": "high", "status": "cancelled"}

        current_user = {"user_id": 3, "role": "admin"}

        result = TaskService.update_task(
            1,
            {"priority": "high", "status": "cancelled"},
            current_user
        )

        assert result["priority"] == "high"
        mock_repo.update.assert_called_once()

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_delete_task_customer_success(self, mock_repo):
        """Customer удаляет свою задачу"""
        mock_repo.get_by_id.return_value = {"task_id": 1, "customer_id": 1}
        mock_repo.delete.return_value = True

        current_user = {"user_id": 1, "role": "customer"}

        result = TaskService.delete_task(1, current_user)

        assert result["message"] == "Task deleted"
        mock_repo.delete.assert_called_once_with(1)

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_delete_task_admin_success(self, mock_repo):
        """Admin удаляет любую задачу"""
        mock_repo.get_by_id.return_value = {"task_id": 1, "customer_id": 5}
        mock_repo.delete.return_value = True

        current_user = {"user_id": 3, "role": "admin"}

        result = TaskService.delete_task(1, current_user)

        assert result["message"] == "Task deleted"

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_delete_task_permission_denied(self, mock_repo):
        """Executor не может удалять задачи"""
        mock_repo.get_by_id.return_value = {"task_id": 1, "customer_id": 5}

        current_user = {"user_id": 2, "role": "executor"}

        with pytest.raises(ValidationError, match="Not enough permissions"):
            TaskService.delete_task(1, current_user)

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_claim_task_success(self, mock_repo):
        """Executor успешно берёт задачу"""
        mock_repo.get_by_id.return_value = {
            "task_id": 1,
            "status": "new",
            "executor_id": None
        }
        mock_repo.update.return_value = {
            "task_id": 1,
            "status": "in_progress",
            "executor_id": 2
        }

        current_user = {"user_id": 2, "role": "executor"}

        result = TaskService.claim_task(1, current_user)

        assert result["status"] == "in_progress"
        assert result["executor_id"] == 2
        mock_repo.update.assert_called_once_with(
            1,
            executor_id=2,
            status="in_progress"
        )

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_claim_task_wrong_role(self, mock_repo):
        """Customer не может брать задачи"""
        current_user = {"user_id": 1, "role": "customer"}

        with pytest.raises(ValidationError, match="Only executors can claim tasks"):
            TaskService.claim_task(1, current_user)

        mock_repo.get_by_id.assert_not_called()

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_claim_task_not_new_status(self, mock_repo):
        """Нельзя взять задачу не в статусе 'new'"""
        mock_repo.get_by_id.return_value = {
            "task_id": 1,
            "status": "in_progress",
            "executor_id": None
        }

        current_user = {"user_id": 2, "role": "executor"}

        with pytest.raises(ValidationError, match="Cannot claim task with status"):
            TaskService.claim_task(1, current_user)

    @patch("databases.business_todo.src.services.task_service.TaskRepository")
    def test_claim_task_already_assigned(self, mock_repo):
        """Задача уже назначена другому исполнителю"""
        mock_repo.get_by_id.return_value = {
            "task_id": 1,
            "status": "new",
            "executor_id": 5
        }

        current_user = {"user_id": 2, "role": "executor"}

        with pytest.raises(ValidationError, match="already assigned"):
            TaskService.claim_task(1, current_user)


class TestAuthService:
    """Тесты для AuthService"""

    @patch("databases.business_todo.src.services.auth_service.UserRepository")
    @patch("databases.business_todo.src.services.auth_service.TokenRepository")
    @patch("databases.business_todo.src.services.auth_service.verify_password")
    @patch("databases.business_todo.src.services.auth_service.create_access_token")
    @patch("databases.business_todo.src.services.auth_service.create_refresh_token")
    def test_login_success(
            self, mock_refresh, mock_access, mock_verify, mock_token_repo, mock_user_repo
    ):
        """Успешный вход"""
        mock_user_repo.get_by_email.return_value = {
            "user_id": 1,
            "email": "test@test.com",
            "password_hash": "hashed",
            "role": "customer",
            "status": "active"
        }
        mock_verify.return_value = True
        mock_access.return_value = "access_token"
        mock_refresh.return_value = "refresh_token"

        result = AuthService.login("test@test.com", "password123")

        assert result["accessToken"] == "access_token"
        assert result["refreshToken"] == "refresh_token"
        assert "user" in result
        assert result["user"]["email"] == "test@test.com"
        mock_token_repo.create.assert_called_once()

    @patch("databases.business_todo.src.services.auth_service.UserRepository")
    def test_login_invalid_credentials(self, mock_user_repo):
        """Неверный пароль"""
        mock_user_repo.get_by_email.return_value = {
            "user_id": 1,
            "password_hash": "hashed"
        }

        with patch(
                "databases.business_todo.src.services.auth_service.verify_password",
                return_value=False
        ):
            with pytest.raises(ValidationError, match="Invalid credentials"):
                AuthService.login("test@test.com", "wrong_password")

    @patch("databases.business_todo.src.services.auth_service.UserRepository")
    def test_login_user_not_found(self, mock_user_repo):
        """Пользователь не найден"""
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(ValidationError, match="Invalid credentials"):
            AuthService.login("unknown@test.com", "password")

    @patch("databases.business_todo.src.services.auth_service.UserRepository")
    def test_login_blocked_user(self, mock_user_repo):
        """Аккаунт заблокирован"""
        mock_user_repo.get_by_email.return_value = {
            "user_id": 1,
            "email": "test@test.com",
            "password_hash": "hashed",
            "status": "blocked"
        }

        with patch(
                "databases.business_todo.src.services.auth_service.verify_password",
                return_value=True
        ):
            with pytest.raises(ValidationError, match="blocked"):
                AuthService.login("test@test.com", "password")

    @patch("databases.business_todo.src.services.auth_service.UserRepository")
    @patch("databases.business_todo.src.services.auth_service.TokenRepository")
    @patch("databases.business_todo.src.services.auth_service.get_password_hash")
    @patch("databases.business_todo.src.services.auth_service.create_access_token")
    @patch("databases.business_todo.src.services.auth_service.create_refresh_token")
    def test_register_success(
            self, mock_refresh, mock_access, mock_hash, mock_token_repo, mock_user_repo
    ):
        """Успешная регистрация"""
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = {
            "user_id": 1,
            "email": "new@test.com",
            "role": "customer",
            "status": "active"
        }
        mock_hash.return_value = "hashed_password"
        mock_access.return_value = "access_token"
        mock_refresh.return_value = "refresh_token"

        result = AuthService.register(
            first_name="Test",
            last_name="User",
            email="new@test.com",
            password="password123",
            phone="+79991234567",
            role="customer"
        )

        assert result["accessToken"] == "access_token"
        assert result["user"]["email"] == "new@test.com"
        mock_user_repo.create.assert_called_once()
        mock_token_repo.create.assert_called_once()

    @patch("databases.business_todo.src.services.auth_service.UserRepository")
    def test_register_email_exists(self, mock_user_repo):
        """Email уже зарегистрирован"""
        mock_user_repo.get_by_email.return_value = {"user_id": 1, "email": "exists@test.com"}

        with pytest.raises(ValidationError, match="Email already registered"):
            AuthService.register(
                first_name="Test",
                last_name="User",
                email="exists@test.com",
                password="password123"
            )

    @patch("databases.business_todo.src.services.auth_service.UserRepository")
    def test_register_invalid_role(self, mock_user_repo):
        """Недопустимая роль при регистрации"""
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(ValidationError, match="Invalid role"):
            AuthService.register(
                first_name="Test",
                last_name="User",
                email="test@test.com",
                password="password123",
                role="admin"  # Нельзя зарегистрироваться как admin
            )

    @patch("databases.business_todo.src.services.auth_service.TokenRepository")
    def test_logout_success(self, mock_token_repo):
        """Успешный выход"""
        result = AuthService.logout(user_id=1)

        assert result["message"] == "Logged out"
        mock_token_repo.delete_by_user_id.assert_called_once_with(1)

    @patch("databases.business_todo.src.services.auth_service.UserRepository")
    @patch("databases.business_todo.src.services.auth_service.TokenRepository")
    @patch("databases.business_todo.src.services.auth_service.decode_token")
    @patch("databases.business_todo.src.services.auth_service.create_access_token")
    def test_refresh_token_success(
            self, mock_access, mock_decode, mock_token_repo, mock_user_repo
    ):
        """Успешное обновление токена"""
        mock_decode.return_value = {"sub": "1", "type": "refresh"}
        mock_token_repo.get_by_token.return_value = {"user_id": 1}
        mock_user_repo.get_by_id.return_value = {
            "user_id": 1,
            "role": "customer"
        }
        mock_access.return_value = "new_access_token"

        result = AuthService.refresh_token("refresh_token_123")

        assert result["accessToken"] == "new_access_token"
        mock_decode.assert_called_once_with("refresh_token_123")

    @patch("databases.business_todo.src.services.auth_service.decode_token")
    def test_refresh_token_invalid(self, mock_decode):
        """Невалидный refresh токен"""
        mock_decode.return_value = None

        with pytest.raises(ValidationError, match="Invalid refresh token"):
            AuthService.refresh_token("invalid_token")

    @patch("databases.business_todo.src.services.auth_service.decode_token")
    @patch("databases.business_todo.src.services.auth_service.TokenRepository")
    def test_refresh_token_not_found(self, mock_token_repo, mock_decode):
        """Refresh токен не найден в БД"""
        mock_decode.return_value = {"sub": "1", "type": "refresh"}
        mock_token_repo.get_by_token.return_value = None

        with pytest.raises(ValidationError, match="not found or expired"):
            AuthService.refresh_token("expired_token")


class TestUserService:
    """Тесты для UserService"""

    @patch("databases.business_todo.src.services.user_service.UserRepository")
    def test_get_me_success(self, mock_repo):
        """Получение своего профиля"""
        mock_repo.get_by_id.return_value = {
            "user_id": 1,
            "email": "test@test.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": "hashed"
        }

        result = UserService.get_me(1)

        assert result["email"] == "test@test.com"
        assert "password_hash" not in result

    @patch("databases.business_todo.src.services.user_service.UserRepository")
    def test_get_me_not_found(self, mock_repo):
        """Пользователь не найден"""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(ValidationError, match="User not found"):
            UserService.get_me(999)

    @patch("databases.business_todo.src.services.user_service.UserRepository")
    def test_get_users_admin_success(self, mock_repo):
        """Admin получает список пользователей"""
        mock_repo.get_all.return_value = [
            {"user_id": 1, "email": "a@test.com", "password_hash": "h1"},
            {"user_id": 2, "email": "b@test.com", "password_hash": "h2"}
        ]

        current_user = {"user_id": 3, "role": "admin"}

        result = UserService.get_users(current_user=current_user)

        assert len(result["users"]) == 2
        assert all("password_hash" not in u for u in result["users"])

    @patch("databases.business_todo.src.services.user_service.UserRepository")
    def test_get_users_permission_denied(self, mock_repo):
        """Customer не может получить список всех пользователей"""
        current_user = {"user_id": 1, "role": "customer"}

        with pytest.raises(ValidationError, match="Not enough permissions"):
            UserService.get_users(current_user=current_user)

        mock_repo.get_all.assert_not_called()

    @patch("databases.business_todo.src.services.user_service.UserRepository")
    def test_update_user_own_profile(self, mock_repo):
        """Пользователь обновляет свой профиль"""
        mock_repo.get_by_id.return_value = {"user_id": 1, "email": "old@test.com"}
        mock_repo.get_by_email.return_value = None
        mock_repo.update.return_value = {"user_id": 1, "email": "new@test.com"}

        current_user = {"user_id": 1, "role": "customer"}

        result = UserService.update_user(1, {"email": "new@test.com"}, current_user)

        assert result["email"] == "new@test.com"
        mock_repo.update.assert_called_once()

    @patch("databases.business_todo.src.services.user_service.UserRepository")
    def test_update_user_other_profile_denied(self, mock_repo):
        """Customer не может обновить чужой профиль"""
        mock_repo.get_by_id.return_value = {"user_id": 5, "email": "other@test.com"}

        current_user = {"user_id": 1, "role": "customer"}

        with pytest.raises(ValidationError, match="Not enough permissions"):
            UserService.update_user(5, {"email": "hacked@test.com"}, current_user)

    @patch("databases.business_todo.src.services.user_service.UserRepository")
    def test_update_user_admin_can_update_any(self, mock_repo):
        """Admin может обновить любой профиль"""
        mock_repo.get_by_id.return_value = {"user_id": 5}
        mock_repo.get_by_email.return_value = None
        mock_repo.update.return_value = {"user_id": 5, "status": "blocked"}

        current_user = {"user_id": 3, "role": "admin"}

        result = UserService.update_user(5, {"status": "blocked"}, current_user)

        assert result["status"] == "blocked"

    @patch("databases.business_todo.src.services.user_service.UserRepository")
    def test_update_user_email_unique(self, mock_repo):
        """Нельзя установить уже занятый email"""
        mock_repo.get_by_id.return_value = {"user_id": 1}
        mock_repo.get_by_email.return_value = {"user_id": 2, "email": "taken@test.com"}

        current_user = {"user_id": 1, "role": "customer"}

        with pytest.raises(ValidationError, match="Email already registered"):
            UserService.update_user(1, {"email": "taken@test.com"}, current_user)
