# tests/utils.py
from datetime import datetime, timedelta
import jwt
from databases.business_todo.src.core.config import get_settings


def create_test_token(user_id: int = 1, role: str = "customer", username: str = "testuser"):
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "role": role,
        "username": username,
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "type": "access"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token
