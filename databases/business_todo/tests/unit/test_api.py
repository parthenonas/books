import pytest
from unittest.mock import patch

from databases.business_todo.tests.conftest import create_test_token
from databases.business_todo.src.utils.validators import ValidationError


class TestCreateTask:
    """Тесты для POST /api/v1/tasks/"""

    def test_success(self, client, override_auth):
        """Customer успешно создаёт задачу"""
        override_auth(user_id=1, role="customer")

        with patch("databases.business_todo.src.api.v1.tasks.TaskService") as mock_service:
            mock_service.create_task.return_value = {
                "task_id": 1,
                "task_text": "Найти кота",
                "description": "Рыжий",
                "priority": "low",
                "status": "new",
                "customer_id": 1,
                "executor_id": None,
                "deadline": None,
                "completed_at": None,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }

            token = create_test_token(user_id=1, role="customer")
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {"task_text": "Найти кота", "priority": "low", "description": "Рыжий"}

            response = client.post("/api/v1/tasks/", json=payload, headers=headers)

            assert response.status_code in [200, 201]
            data = response.json()
            assert data["task_text"] == "Найти кота"

    def test_validation_error(self, client, override_auth):
        """Ошибка валидации данных"""
        override_auth(user_id=1, role="customer")

        with patch("databases.business_todo.src.api.v1.tasks.TaskService") as mock_service:
            mock_service.create_task.side_effect = ValidationError("Invalid data")

            token = create_test_token(user_id=1, role="customer")
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {"task_text": "", "priority": "low"}

            response = client.post("/api/v1/tasks/", json=payload, headers=headers)

            assert response.status_code == 422

    def test_wrong_role(self, client, override_auth):
        """Executor не может создавать задачи"""
        override_auth(user_id=2, role="executor")

        with patch("databases.business_todo.src.api.v1.tasks.TaskService") as mock_service:
            mock_service.create_task.side_effect = ValidationError("Not enough permissions")

            token = create_test_token(user_id=2, role="executor")
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {"task_text": "Test", "priority": "low"}

            response = client.post("/api/v1/tasks/", json=payload, headers=headers)

            assert response.status_code == 403


class TestGetTasks:
    """Тесты для GET /api/v1/tasks/"""

    def test_success(self, client, override_auth):
        """Успешное получение списка задач"""
        override_auth(user_id=1, role="customer")

        with patch("databases.business_todo.src.api.v1.tasks.TaskService") as mock_service:
            mock_service.get_tasks.return_value = {"tasks": [], "total": 0, "page": 1, "limit": 20}

            token = create_test_token(user_id=1, role="customer")
            headers = {"Authorization": f"Bearer {token}"}

            response = client.get("/api/v1/tasks/", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert "total" in data


class TestGetTask:
    """Тесты для GET /api/v1/tasks/{id}"""

    def test_not_found(self, client, override_auth):
        """Задача не найдена"""
        override_auth(user_id=1, role="customer")

        with patch("databases.business_todo.src.api.v1.tasks.TaskService") as mock_service:
            mock_service.get_task.side_effect = ValidationError("Task not found")

            token = create_test_token(user_id=1, role="customer")
            headers = {"Authorization": f"Bearer {token}"}

            response = client.get("/api/v1/tasks/999", headers=headers)

            assert response.status_code == 404


class TestDeleteTask:
    """Тесты для DELETE /api/v1/tasks/{id}"""

    def test_success(self, client, override_auth):
        """Admin успешно удаляет задачу"""
        override_auth(user_id=3, role="admin")

        with patch("databases.business_todo.src.api.v1.tasks.TaskService") as mock_service:
            mock_service.delete_task.return_value = {"message": "Task deleted"}

            token = create_test_token(user_id=3, role="admin")
            headers = {"Authorization": f"Bearer {token}"}

            response = client.delete("/api/v1/tasks/1", headers=headers)

            assert response.status_code == 200


class TestClaimTask:
    """Тесты для POST /api/v1/tasks/{id}/claim"""

    def test_success(self, client, override_auth):
        """Executor успешно берёт задачу"""
        override_auth(user_id=2, role="executor")

        with patch("databases.business_todo.src.api.v1.tasks.TaskService") as mock_service:
            mock_service.claim_task.return_value = {
                "task_id": 1,
                "task_text": "Test task",
                "description": None,
                "customer_id": 1,
                "executor_id": 2,
                "status": "in_progress",
                "priority": "medium",
                "deadline": None,
                "completed_at": None,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }

            token = create_test_token(user_id=2, role="executor")
            headers = {"Authorization": f"Bearer {token}"}

            response = client.post("/api/v1/tasks/1/claim", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "in_progress"
            assert data["executor_id"] == 2

    def test_wrong_role(self, client, override_auth):
        """Customer не может брать задачи"""
        override_auth(user_id=1, role="customer")

        with patch("databases.business_todo.src.api.v1.tasks.TaskService") as mock_service:
            mock_service.claim_task.side_effect = ValidationError("Only executors can claim tasks")

            token = create_test_token(user_id=1, role="customer")
            headers = {"Authorization": f"Bearer {token}"}

            response = client.post("/api/v1/tasks/1/claim", headers=headers)

            assert response.status_code == 400

    def test_already_assigned(self, client, override_auth):
        """Задача уже назначена другому"""
        override_auth(user_id=2, role="executor")

        with patch("databases.business_todo.src.api.v1.tasks.TaskService") as mock_service:
            mock_service.claim_task.side_effect = ValidationError(
                "Task is already assigned to another executor"
            )

            token = create_test_token(user_id=2, role="executor")
            headers = {"Authorization": f"Bearer {token}"}

            response = client.post("/api/v1/tasks/1/claim", headers=headers)

            assert response.status_code == 409
