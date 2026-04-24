import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from databases.business_todo.src.repositories.user_repo import UserRepository
from databases.business_todo.src.repositories.task_repo import TaskRepository
from databases.business_todo.src.repositories.token_repo import TokenRepository
from databases.business_todo.src.db.context import get_db_cursor


class TestUserRepository:
    """Тесты для UserRepository"""

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_get_by_id_success(self, mock_cursor_factory):
        """Получение пользователя по ID"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "email": "test@test.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "customer",
            "status": "active"
        }
        mock_cursor_factory.return_value = mock_cursor

        user = UserRepository.get_by_id(1)

        assert user["user_id"] == 1
        assert user["email"] == "test@test.com"
        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "SELECT" in sql
        assert "users" in sql
        assert "user_id" in sql

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_get_by_id_not_found(self, mock_cursor_factory):
        """Пользователь не найден"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_cursor_factory.return_value = mock_cursor

        user = UserRepository.get_by_id(999)

        assert user is None

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_get_by_email_success(self, mock_cursor_factory):
        """Получение пользователя по email"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "email": "test@test.com",
            "password_hash": "hashed"
        }
        mock_cursor_factory.return_value = mock_cursor

        user = UserRepository.get_by_email("test@test.com")

        assert user["email"] == "test@test.com"
        sql = mock_cursor.execute.call_args[0][0]
        assert "email" in sql

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_get_by_email_not_found(self, mock_cursor_factory):
        """Email не найден"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_cursor_factory.return_value = mock_cursor

        user = UserRepository.get_by_email("unknown@test.com")

        assert user is None

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_get_all_no_filters(self, mock_cursor_factory):
        """Получение всех пользователей без фильтров"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {"user_id": 1, "email": "a@test.com"},
            {"user_id": 2, "email": "b@test.com"}
        ]
        mock_cursor_factory.return_value = mock_cursor

        users = UserRepository.get_all()

        assert len(users) == 2
        sql = mock_cursor.execute.call_args[0][0]
        assert "SELECT" in sql
        assert "WHERE 1=1" in sql

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_get_all_with_role_filter(self, mock_cursor_factory):
        """Фильтр по роли"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"user_id": 1, "role": "customer"}]
        mock_cursor_factory.return_value = mock_cursor

        users = UserRepository.get_all(role="customer")

        assert len(users) == 1
        sql = mock_cursor.execute.call_args[0][0]
        assert "role" in sql

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_get_all_with_status_filter(self, mock_cursor_factory):
        """Фильтр по статусу"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"user_id": 1, "status": "active"}]
        mock_cursor_factory.return_value = mock_cursor

        users = UserRepository.get_all(status="active")

        assert len(users) == 1
        sql = mock_cursor.execute.call_args[0][0]
        assert "status" in sql

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_create_success(self, mock_cursor_factory):
        """Создание пользователя"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "email": "new@test.com",
            "role": "customer",
            "status": "active"
        }
        mock_cursor_factory.return_value = mock_cursor

        user = UserRepository.create(
            first_name="Test",
            last_name="User",
            email="new@test.com",
            password_hash="hashed",
            phone="+79991234567",
            role="customer"
        )

        assert user["user_id"] == 1
        assert user["status"] == "active"
        sql = mock_cursor.execute.call_args[0][0]
        assert "INSERT" in sql
        assert "users" in sql
        assert "RETURNING" in sql

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_update_success(self, mock_cursor_factory):
        """Обновление пользователя"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "email": "updated@test.com",
            "first_name": "Updated"
        }
        mock_cursor_factory.return_value = mock_cursor

        user = UserRepository.update(1, email="updated@test.com", first_name="Updated")

        assert user["email"] == "updated@test.com"
        sql = mock_cursor.execute.call_args[0][0]
        assert "UPDATE" in sql
        assert "WHERE user_id" in sql
        assert "RETURNING" in sql

    @patch("databases.business_todo.src.repositories.user_repo.get_db_cursor")
    def test_update_no_fields(self, mock_cursor_factory):
        """Обновление без полей возвращает текущего пользователя"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"user_id": 1, "email": "test@test.com"}
        mock_cursor_factory.return_value = mock_cursor

        user = UserRepository.update(1)

        assert user["user_id"] == 1
        sql = mock_cursor.execute.call_args[0][0]
        assert "SELECT" in sql


class TestTaskRepository:
    """Тесты для TaskRepository"""

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_get_by_id_success(self, mock_cursor_factory):
        """Получение задачи по ID"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "task_id": 1,
            "task_text": "Test task",
            "status": "new",
            "customer_id": 1,
            "executor_id": None
        }
        mock_cursor_factory.return_value = mock_cursor

        task = TaskRepository.get_by_id(1)

        assert task["task_id"] == 1
        assert task["status"] == "new"
        sql = mock_cursor.execute.call_args[0][0]
        assert "JOIN" in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_get_by_id_not_found(self, mock_cursor_factory):
        """Задача не найдена"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_cursor_factory.return_value = mock_cursor

        task = TaskRepository.get_by_id(999)

        assert task is None

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_get_all_no_filters(self, mock_cursor_factory):
        """Получение всех задач без фильтров"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {"task_id": 1, "task_text": "Task 1"},
            {"task_id": 2, "task_text": "Task 2"}
        ]
        mock_cursor.fetchone.return_value = {"count": 2}
        mock_cursor_factory.return_value = mock_cursor

        tasks, total = TaskRepository.get_all()

        assert len(tasks) == 2
        assert total == 2

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_get_all_with_status_filter(self, mock_cursor_factory):
        """Фильтр по статусу"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"task_id": 1, "status": "new"}]
        mock_cursor.fetchone.return_value = {"count": 1}
        mock_cursor_factory.return_value = mock_cursor

        tasks, total = TaskRepository.get_all(status="new")

        assert len(tasks) == 1
        sql = mock_cursor.execute.call_args[0][0]
        assert "status" in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_get_all_with_priority_filter(self, mock_cursor_factory):
        """Фильтр по приоритету"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"task_id": 1, "priority": "high"}]
        mock_cursor.fetchone.return_value = {"count": 1}
        mock_cursor_factory.return_value = mock_cursor

        tasks, total = TaskRepository.get_all(priority="high")

        assert len(tasks) == 1
        sql = mock_cursor.execute.call_args[0][0]
        assert "priority" in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_get_all_with_customer_id_filter(self, mock_cursor_factory):
        """Фильтр по заказчику"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"task_id": 1, "customer_id": 5}]
        mock_cursor.fetchone.return_value = {"count": 1}
        mock_cursor_factory.return_value = mock_cursor

        tasks, total = TaskRepository.get_all(customer_id=5)

        assert len(tasks) == 1
        sql = mock_cursor.execute.call_args[0][0]
        assert "customer_id" in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_get_all_with_executor_id_filter(self, mock_cursor_factory):
        """Фильтр по исполнителю"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"task_id": 1, "executor_id": 2}]
        mock_cursor.fetchone.return_value = {"count": 1}
        mock_cursor_factory.return_value = mock_cursor

        tasks, total = TaskRepository.get_all(executor_id=2)

        assert len(tasks) == 1
        sql = mock_cursor.execute.call_args[0][0]
        assert "executor_id" in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_get_all_with_pagination(self, mock_cursor_factory):
        """Пагинация"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"task_id": i} for i in range(1, 11)]
        mock_cursor.fetchone.return_value = {"count": 100}
        mock_cursor_factory.return_value = mock_cursor

        tasks, total = TaskRepository.get_all(page=2, limit=10)

        assert len(tasks) == 10
        assert total == 100
        call_args = mock_cursor.execute.call_args[0]
        assert "LIMIT" in call_args[0]
        assert "OFFSET" in call_args[0]

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_create_success(self, mock_cursor_factory):
        """Создание задачи"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "task_id": 1,
            "task_text": "New task",
            "status": "new",
            "customer_id": 1
        }
        mock_cursor_factory.return_value = mock_cursor

        task = TaskRepository.create(
            task_text="New task",
            description="Description",
            customer_id=1,
            priority="medium",
            deadline=None
        )

        assert task["task_id"] == 1
        assert task["status"] == "new"
        sql = mock_cursor.execute.call_args[0][0]
        assert "INSERT" in sql
        assert "tasks" in sql
        assert "RETURNING" in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_update_success(self, mock_cursor_factory):
        """Обновление задачи"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "task_id": 1,
            "status": "in_progress",
            "executor_id": 2
        }
        mock_cursor_factory.return_value = mock_cursor

        task = TaskRepository.update(1, status="in_progress", executor_id=2)

        assert task["status"] == "in_progress"
        sql = mock_cursor.execute.call_args[0][0]
        assert "UPDATE" in sql
        assert "WHERE task_id" in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_update_sets_completed_at(self, mock_cursor_factory):
        """При статусе completed устанавливается completed_at"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"task_id": 1, "status": "completed"}
        mock_cursor_factory.return_value = mock_cursor

        TaskRepository.update(1, status="completed")

        call_args = mock_cursor.execute.call_args[0]
        params = call_args[1]
        sql = call_args[0]
        assert "completed_at" in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_update_no_fields(self, mock_cursor_factory):
        """Обновление без полей возвращает текущую задачу"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"task_id": 1, "status": "new"}
        mock_cursor_factory.return_value = mock_cursor

        task = TaskRepository.update(1)

        assert task["task_id"] == 1
        sql = mock_cursor.execute.call_args[0][0]
        assert "SELECT" in sql
        assert "UPDATE" not in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_delete_success(self, mock_cursor_factory):
        """Удаление задачи"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 1
        mock_cursor_factory.return_value = mock_cursor

        result = TaskRepository.delete(1)

        assert result is True
        sql = mock_cursor.execute.call_args[0][0]
        assert "DELETE" in sql
        assert "WHERE task_id" in sql

    @patch("databases.business_todo.src.repositories.task_repo.get_db_cursor")
    def test_delete_not_found(self, mock_cursor_factory):
        """Удаление несуществующей задачи"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 0
        mock_cursor_factory.return_value = mock_cursor

        result = TaskRepository.delete(999)

        assert result is False


class TestTokenRepository:
    """Тесты для TokenRepository"""

    @patch("databases.business_todo.src.repositories.token_repo.get_db_cursor")
    def test_create_success(self, mock_cursor_factory):
        """Создание refresh токена"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "token_id": 1,
            "user_id": 1,
            "token": "refresh_token_123"
        }
        mock_cursor_factory.return_value = mock_cursor

        token = TokenRepository.create(
            user_id=1,
            token="refresh_token_123",
            expires_days=7
        )

        assert token["token_id"] == 1
        sql = mock_cursor.execute.call_args[0][0]
        assert "INSERT" in sql
        assert "refresh_tokens" in sql

    @patch("databases.business_todo.src.repositories.token_repo.get_db_cursor")
    def test_get_by_token_success(self, mock_cursor_factory):
        """Получение токена по значению"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "token_id": 1,
            "user_id": 1,
            "token": "refresh_token_123"
        }
        mock_cursor_factory.return_value = mock_cursor

        token = TokenRepository.get_by_token("refresh_token_123")

        assert token["token"] == "refresh_token_123"
        sql = mock_cursor.execute.call_args[0][0]
        assert "token" in sql

    @patch("databases.business_todo.src.repositories.token_repo.get_db_cursor")
    def test_get_by_token_not_found(self, mock_cursor_factory):
        """Токен не найден"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_cursor_factory.return_value = mock_cursor

        token = TokenRepository.get_by_token("invalid_token")

        assert token is None

    @patch("databases.business_todo.src.repositories.token_repo.get_db_cursor")
    def test_delete_by_user_id_success(self, mock_cursor_factory):
        """Удаление токенов пользователя"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 2
        mock_cursor_factory.return_value = mock_cursor

        result = TokenRepository.delete_by_user_id(1)

        assert result == 2
        sql = mock_cursor.execute.call_args[0][0]
        assert "DELETE" in sql
        assert "user_id" in sql

    @patch("databases.business_todo.src.repositories.token_repo.get_db_cursor")
    def test_delete_by_user_id_no_tokens(self, mock_cursor_factory):
        """У пользователя нет токенов"""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 0
        mock_cursor_factory.return_value = mock_cursor

        result = TokenRepository.delete_by_user_id(999)

        assert result == 0
