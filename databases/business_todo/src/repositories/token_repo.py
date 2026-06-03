from datetime import datetime, timedelta
from typing import Optional

from databases.business_todo.src.db.context import get_db_cursor


class TokenRepository:
    @staticmethod
    def create(user_id: int, token: str, expires_days: int = 7) -> dict:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        with get_db_cursor() as cursor:
            cursor.execute(
                """INSERT INTO refresh_tokens (user_id, token, expires_at, created_at)
                   VALUES (%s, %s, %s, %s)
                   RETURNING *""",
                (user_id, token, expires_at, datetime.utcnow())
            )
            return cursor.fetchone()

    @staticmethod
    def get_by_token(token: str) -> Optional[dict]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM refresh_tokens WHERE token = %s AND expires_at > %s",
                (token, datetime.utcnow())
            )
            return cursor.fetchone()

    @staticmethod
    def delete_by_user_id(user_id: int) -> int:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM refresh_tokens WHERE user_id = %s", (user_id,))
            return cursor.rowcount

    @staticmethod
    def delete(token: str) -> bool:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM refresh_tokens WHERE token = %s", (token,))
            return cursor.rowcount > 0
