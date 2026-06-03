import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import jwt
import pytest
from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

os.environ["DB_NAME"] = "test_task_pool"

# Мокаем psycopg2.connect ДО импорта приложения
with patch("psycopg2.connect") as mock_connect:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    from databases.business_todo.src.main import app
    from databases.business_todo.src.core.config import get_settings
    from databases.business_todo.src.api.dependencies import get_current_user


@pytest.fixture(scope="session")
def test_settings():
    return get_settings()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def override_auth():
    def _override(user_id: int = 1, role: str = "customer"):
        async def mock_get_current_user():
            return {
                "user_id": user_id,
                "role": role,
                "email": "test@test.com",
                "status": "active",
                "first_name": "Test",
                "last_name": "User"
            }

        app.dependency_overrides[get_current_user] = mock_get_current_user

    return _override


@pytest.fixture(autouse=True)
def cleanup_dependencies():
    """Очищает dependency_overrides после каждого теста"""
    yield
    app.dependency_overrides.clear()


def create_test_token(user_id: int = 1, role: str = "customer"):
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "type": "access"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.fixture
def auth_headers():
    token = create_test_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
