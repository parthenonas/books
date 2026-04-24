from typing import Optional, List, Tuple
from datetime import datetime
from databases.business_todo.src.db.context import get_db_cursor


class TaskRepository:
    @staticmethod
    def get_all(
            status: Optional[str] = None,
            priority: Optional[str] = None,
            customer_id: Optional[int] = None,
            executor_id: Optional[int] = None,
            page: int = 1,
            limit: int = 20
    ) -> Tuple[List[dict], int]:
        query = """
            SELECT t.*, 
                   c.first_name as customer_first_name, c.last_name as customer_last_name, c.email as customer_email,
                   e.first_name as executor_first_name, e.last_name as executor_last_name, e.email as executor_email
            FROM tasks t
            LEFT JOIN users c ON t.customer_id = c.user_id
            LEFT JOIN users e ON t.executor_id = e.user_id
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND t.status = %s"
            params.append(status)
        if priority:
            query += " AND t.priority = %s"
            params.append(priority)
        if customer_id:
            query += " AND t.customer_id = %s"
            params.append(customer_id)
        if executor_id:
            query += " AND t.executor_id = %s"
            params.append(executor_id)

        count_query = f"SELECT COUNT(*) FROM tasks WHERE 1=1" + query.split("WHERE 1=1")[1]

        with get_db_cursor() as cursor:
            cursor.execute(count_query.replace("t.*", "1"), params)
            total = cursor.fetchone()["count"]
            query += " ORDER BY t.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, (page - 1) * limit])
            cursor.execute(query, params)
            tasks = cursor.fetchall()

        return tasks, total

    @staticmethod
    def get_by_id(task_id: int) -> Optional[dict]:
        with get_db_cursor() as cursor:
            cursor.execute(
                """SELECT t.*, 
                          c.first_name as customer_first_name, c.last_name as customer_last_name, c.email as customer_email,
                          e.first_name as executor_first_name, e.last_name as executor_last_name, e.email as executor_email
                   FROM tasks t
                   LEFT JOIN users c ON t.customer_id = c.user_id
                   LEFT JOIN users e ON t.executor_id = e.user_id
                   WHERE t.task_id = %s""",
                (task_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def create(task_text: str, description: str, customer_id: int, priority: str,
               deadline: Optional[str]) -> dict:
        now = datetime.utcnow()
        with get_db_cursor() as cursor:
            cursor.execute(
                """INSERT INTO tasks (task_text, description, customer_id, priority, deadline, status, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, 'new', %s, %s)
                   RETURNING *""",
                (task_text, description, customer_id, priority, deadline, now, now)
            )
            return cursor.fetchone()

    @staticmethod
    def update(task_id: int, **kwargs) -> Optional[dict]:
        if not kwargs:
            return TaskRepository.get_by_id(task_id)

        if kwargs.get("status") == "completed":
            kwargs["completed_at"] = datetime.utcnow()

        kwargs["updated_at"] = datetime.utcnow()
        fields = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        values = list(kwargs.values()) + [task_id]

        with get_db_cursor() as cursor:
            cursor.execute(
                f"UPDATE tasks SET {fields} WHERE task_id = %s RETURNING *",
                values
            )
            return cursor.fetchone()

    @staticmethod
    def delete(task_id: int) -> bool:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM tasks WHERE task_id = %s", (task_id,))
            return cursor.rowcount > 0


@staticmethod
def is_available_for_claim(task_id: int) -> bool:
    task = TaskRepository.get_by_id(task_id)
    if not task:
        return False
    return task["status"] == "new" and task["executor_id"] is None
