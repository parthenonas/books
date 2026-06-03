from typing import Optional
from databases.business_todo.src.repositories.task_repo import TaskRepository
from databases.business_todo.src.utils.validators import ValidationError


class TaskService:

    @staticmethod
    def get_tasks(
            status: Optional[str] = None,
            priority: Optional[str] = None,
            customer_id: Optional[int] = None,
            executor_id: Optional[int] = None,
            page: int = 1,
            limit: int = 20
    ) -> dict:
        """Получить список задач с фильтрацией"""
        tasks, total = TaskRepository.get_all(
            status=status,
            priority=priority,
            customer_id=customer_id,
            executor_id=executor_id,
            page=page,
            limit=limit
        )

        for task in tasks:
            if task.get("customer_first_name"):
                task["customer"] = {
                    "user_id": task["customer_id"],
                    "first_name": task["customer_first_name"],
                    "last_name": task["customer_last_name"],
                    "email": task["customer_email"]
                }
                del task["customer_first_name"]
                del task["customer_last_name"]
                del task["customer_email"]

            if task.get("executor_first_name"):
                task["executor"] = {
                    "user_id": task["executor_id"],
                    "first_name": task["executor_first_name"],
                    "last_name": task["executor_last_name"],
                    "email": task["executor_email"]
                }
                del task["executor_first_name"]
                del task["executor_last_name"]
                del task["executor_email"]

        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "limit": limit
        }

    @staticmethod
    def get_task(task_id: int, current_user: dict) -> dict:
        """Получить задачу по ID с проверкой прав"""
        task = TaskRepository.get_by_id(task_id)
        if not task:
            raise ValidationError("Task not found")
        if current_user["role"] == "executor" and task["executor_id"] != current_user["user_id"]:
            raise ValidationError("Not enough permissions")

        if task.get("customer_first_name"):
            task["customer"] = {
                "user_id": task["customer_id"],
                "first_name": task["customer_first_name"],
                "last_name": task["customer_last_name"],
                "email": task["customer_email"]
            }
            del task["customer_first_name"]
            del task["customer_last_name"]
            del task["customer_email"]

        if task.get("executor_first_name"):
            task["executor"] = {
                "user_id": task["executor_id"],
                "first_name": task["executor_first_name"],
                "last_name": task["executor_last_name"],
                "email": task["executor_email"]
            }
            del task["executor_first_name"]
            del task["executor_last_name"]
            del task["executor_email"]

        return task

    @staticmethod
    def create_task(
            task_text: str,
            priority: str,
            description: Optional[str] = None,
            deadline: Optional[str] = None,
            current_user: Optional[dict] = None
    ) -> dict:
        """Создать задачу (только customer/admin)"""
        if current_user["role"] not in ["admin", "customer"]:
            raise ValidationError("Not enough permissions to create tasks")
        task = TaskRepository.create(
            task_text=task_text,
            description=description,
            customer_id=current_user["user_id"],
            priority=priority,
            deadline=deadline
        )
        return task

    @staticmethod
    def update_task(task_id: int, update_data: dict, current_user: dict
                    ) -> dict:
        """Обновить задачу с проверкой прав по ролям"""
        task = TaskRepository.get_by_id(task_id)

        if not task:
            raise ValidationError("Task not found")

        if current_user["role"] == "admin":
            allowed_fields = ["task_text", "description", "priority",
                              "deadline", "executor_id", "status"]
        elif current_user["role"] == "customer":
            if task["customer_id"] != current_user["user_id"]:
                raise ValidationError("Not your task")
            allowed_fields = ["task_text", "description", "priority", "deadline"]
        elif current_user["role"] == "executor":
            if task["executor_id"] != current_user["user_id"]:
                raise ValidationError("Not your task")
            allowed_fields = ["status"]
        else:
            raise ValidationError("Not enough permissions")

        validated = {}
        for field, value in update_data.items():
            if value is None:
                continue
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update {field}")
            validated[field] = value

        if not validated:
            return task

        return TaskRepository.update(task_id, **validated)


    @staticmethod
    def delete_task(task_id: int, current_user: dict) -> dict:
        """Удалить задачу (владелец или admin)"""
        task = TaskRepository.get_by_id(task_id)

        if not task:
            raise ValidationError("Task not found")

        if current_user["role"] != "admin" and task["customer_id"] != current_user["user_id"]:
            raise ValidationError("Not enough permissions")

        TaskRepository.delete(task_id)
        return {"message": "Task deleted"}


    @staticmethod
    def claim_task(task_id: int, current_user: dict) -> dict:
        if current_user["role"] != "executor":
            raise ValidationError("Only executors can claim tasks")

        task = TaskRepository.get_by_id(task_id)
        if not task:
            raise ValidationError("Task not found")

        if task["status"] != "new":
            raise ValidationError(f"Cannot claim task with status '{task['status']}'")

        if task["executor_id"] is not None and task["executor_id"] != current_user["user_id"]:
            raise ValidationError("Task is already assigned to another executor")

        updated = TaskRepository.update(
            task_id,
            executor_id=current_user["user_id"],
            status="in_progress"
        )

        return updated
