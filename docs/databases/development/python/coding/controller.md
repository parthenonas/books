# Разработка слоя контроллеров web-приложения

Контроллеры (обычно называют API routes) — это слой, который принимает HTTP-запросы от клиента и возвращает ответы. Контроллер — это "входная дверь" вашего приложения.

На этом этапе мы разработаем контроллеры для трёх основных функций:

1. **Аутентификация** — вход, регистрация, выход.
2. **Управление пользователями** — получение профиля, список пользователей.
3. **Управление задачами** — создание, получение, обновление, отмена задач.

## Подготовка: зависимости (Dependencies)

До того как написать контроллеры, нам нужно подготовить **зависимости** для проверки авторизации. В FastAPI это делается через специальный механизм `Depends`.

Создайте файл `src/api/dependencies.py`:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.security import decode_token
from repositories.user_repo import UserRepository

security = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Зависимость для получения текущего пользователя из JWT токена.
    Используется во всех защищённых контроллерах.
    """
    token = credentials.credentials

    # Декодируем JWT
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Получаем пользователя из БД
    user = UserRepository.get_by_id(int(user_id))
    if not user or user["status"] != "active":
        raise HTTPException(status_code=401, detail="User not found or blocked")

    return user
```

### Что здесь происходит?

```python
def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
```

- `Depends(security)` — автоматически извлекает токен из заголовка `Authorization: Bearer <token>`.
- Так как наш репозиторий использует синхронный psycopg2, FastAPI автоматически запустит эту функцию в отдельном пуле потоков (threadpool), чтобы запрос к БД не заблокировал весь сервер.

```python
    token = credentials.credentials
    payload = decode_token(token)
```

- Извлекаем токен и декодируем его (проверяем подпись и срок действия).

```python
    user = UserRepository.get_by_id(int(user_id))
    if not user or user["status"] != "active":
        raise HTTPException(status_code=401, detail="User not found or blocked")
```

- Получаем пользователя из БД и проверяем, активен ли он.
- Если не активен — возвращаем ошибку 401.

::: details Как использовать зависимость?

```python
@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    # current_user уже содержит данные пользователя!
    return {"user_id": current_user["user_id"]}
```

FastAPI автоматически вызовет `get_current_user`, проверит токен, и если всё хорошо — передаст пользователя в контроллер.

```mermaid
flowchart TD
  A[Клиент отправляет запрос] --> B{Depends: get_current_user}
  B -- Нет токена или некорректный --> C[Ответ 401 Unauthorized]
  B -- Токен валиден --> D{Depends: verify_same_user?}

  D -- Не требуется --> E[Передача запроса в контроллер]
  D -- Требуется --> F{ID в URL = ID в токене?}

  F -- Нет --> C
  F -- Да --> E
```

:::

## Контроллеры аутентификации

Контроллеры аутентификации отвечают за вход и регистрацию. Это **публичные** эндпоинты — не требуют авторизации ( кроме эндпоинта `/api/v1/logout`, так как данный эндпоинт понимает какому пользователю надо закончить сессию, исходя из данных, полученных из токена ).

Создайте файл `src/api/v1/auth.py`:

```python
from fastapi import APIRouter, HTTPException, status, Depends

from api.dependencies import get_current_user
from services.auth_service import AuthService
from utils.validators import ValidationError
from schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """
    Вход в систему.

    Требует:
    - **email**: Почта пользователя
    - **password**: Пароль

    Возвращает:
    - **accessToken**: Токен для доступа к API (действителен 15 минут)
    - **refreshToken**: Токен для обновления (действителен 7 дней)
    - **user**: Данные пользователя
    """
    try:
        return AuthService.login(email=request.email, password=request.password)
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    """
    Регистрация нового пользователя.

    Требует:
    - **email**: Уникальная почта
    - **password**: Пароль (минимум 6 символов)
    - **first_name**: Имя
    - **last_name**: Фамилия
    - **phone**: Телефон (опционально)
    - **role**: Роль (customer или executor)

    При регистрации статус автоматически становится **active**.
    """
    try:
        return AuthService.register(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            password=request.password,
            phone=request.phone,
            role=request.role
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """
    Выход из системы.

    Удаляет refresh token, делая невозможным получение новых access токенов.
    Текущий access token будет действовать до истечения срока (обычно 15 минут).
    """
    try:
        return AuthService.logout(current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh(request: RefreshTokenRequest):
    """
    Обновление access token.

    Требует:
    - **refreshToken**: Refresh token, полученный при входе/регистрации

    Возвращает новый **accessToken** без необходимости повторного входа.
    """
    try:
        return AuthService.refresh_token(request.refreshToken)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
```

### Разбор контроллера `/login`

```python
@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
```

- `@router.post("/login")` — регистрирует POST эндпоинт `/api/v1/auth/login`.
- `response_model=TokenResponse` — FastAPI автоматически валидирует и форматирует ответ.
- `request: LoginRequest` — FastAPI парсит JSON тело запроса в объект `LoginRequest` (Pydantic автоматически парсит и валидирует).

```python
    try:
        return AuthService.login(email=request.email, password=request.password)
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
```

- Вызываем сервис авторизации.
- Если возникло исключение (неверный пароль и т.д.) — возвращаем ошибку 401 (Unauthorized).

## Схемы валидации (DTO)

Перед тем как писать остальные контроллеры, нам нужны **Pydantic-модели** (DTO) для валидации входных данных.

DTO (Data Transfer Object) в роутерах FastAPI — это по сути «чёткое описание того, какие данные ты принимаешь и отдаёшь через API». Очень простыми словами: это как форма с полями, которую клиент должен заполнить, и ты заранее говоришь — какие поля есть, какого они типа и какие обязательны. Без DTO ты бы просто принимал «что угодно» (например, сырой JSON) и потом вручную проверял, есть ли нужные ключи, правильные ли там типы, не забыли ли что-то. DTO делает это автоматически: валидирует входящие данные, превращает их в удобные объекты и сразу отсекает неправильные запросы с понятной ошибкой. Плюс это делает код чище — роутер не занимается проверками, а просто получает уже готовые, корректные данные, и ещё даёт бесплатную документацию API (Swagger), потому что схема данных уже описана.

Создайте файл `src/schemas/auth.py`:

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)


class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    role: str = Field(default="customer", pattern="^(customer|executor)$")


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refreshToken: str


class RefreshTokenResponse(BaseModel):
    accessToken: str
    expiresIn: int
```

### Что такое эти классы?

Pydantic-модели (DTO):

- **Валидируют** входные данные автоматически.
- **Генерируют** документацию для Swagger/OpenAPI.
- **Преобразуют** данные в нужные типы.

Примеры:

| Правило                     | Описание                             |
| --------------------------- | ------------------------------------ |
| `Field(..., min_length=6)`  | Строка мин 6 символов                |
| `Field(default="customer")` | Значение по умолчанию                |
| `EmailStr`                  | Автоматически проверяет формат почты |
| `Optional[str]`             | Поле опционально (может быть None)   |

## Контроллеры пользователей

Контроллеры пользователей позволяют получить информацию о пользователе и его профиль.

Создайте файл `src/api/v1/users.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from api.dependencies import get_current_user
from services.user_service import UserService
from utils.validators import ValidationError
from schemas.users import UserUpdate, UserResponse, UserListResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Получить профиль текущего пользователя.

    Требует авторизации (Bearer token в заголовке Authorization).
    """
    try:
        return UserService.get_me(current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=UserListResponse)
def get_users(
        role: Optional[str] = None,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
):
    """
    Получить список всех пользователей (только для админов).

    Параметры запроса:
    - **role**: Фильтр по роли (customer, executor, admin)
    - **status**: Фильтр по статусу (active, inactive)
    """
    try:
        return UserService.get_users(role=role, status=status)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
        user_id: int,
        request: UserUpdate,
        current_user: dict = Depends(get_current_user)
):
    """
    Обновить профиль пользователя.

    Права доступа:
    - Пользователь может обновить только свой профиль
    - Admin может обновить любой профиль

    Нельзя изменить:
    - user_id
    - password_hash (используйте отдельный эндпоинт change_password)
    - role
    """
    try:
        if current_user["user_id"] != user_id and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Not enough permissions")

        return UserService.update_profile(
            user_id,
            request.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Важная деталь: `exclude_unset=True`

```python
request.model_dump(exclude_unset=True)
```

Это очень полезный трюк! Если пользователь не передал поле — оно не будет включено в словарь.

**Пример:** Если пользователь отправил только `{"first_name": "John"}`, то словарь будет именно `{"first_name": "John"}`, а не `{"first_name": "John", "last_name": None, "email": None, ...}`.

Это позволяет сервису понять, какие поля действительно нужно обновить.

## Контроллеры задач

Контроллеры задач — самые сложные, так как они должны проверять права доступа.

Создайте файл `src/api/v1/tasks.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from api.dependencies import get_current_user
from services.task_service import TaskService
from utils.validators import ValidationError
from schemas.tasks import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
def get_tasks(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        customer_id: Optional[int] = None,
        executor_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
        current_user: dict = Depends(get_current_user)
):
    """
    Получить список задач с фильтрацией и пагинацией.

    Параметры запроса:
    - **status**: Фильтр по статусу (new, in_progress, completed, cancelled)
    - **priority**: Фильтр по приоритету (low, medium, high)
    - **customer_id**: ID заказчика (задачи этого заказчика)
    - **executor_id**: ID исполнителя (задачи этого исполнителя)
    - **page**: Номер страницы (по умолчанию 1)
    - **limit**: Количество записей на странице (по умолчанию 20)

    Примеры:
    - GET /api/v1/tasks?status=completed — все завершённые задачи
    - GET /api/v1/tasks?page=2&limit=10 — вторая страница, по 10 задач
    - GET /api/v1/tasks?priority=high — все задачи с высоким приоритетом
    """
    try:
        return TaskService.get_tasks(
            status=status,
            priority=priority,
            customer_id=customer_id,
            executor_id=executor_id,
            page=page,
            limit=limit,
            current_user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
        request: TaskCreate,
        current_user: dict = Depends(get_current_user)
):
    """
    Создать новую задачу.

    Требует:
    - **task_text**: Текст задачи (обязательно)
    - **priority**: Приоритет (low, medium, high)
    - **description**: Описание (опционально)
    - **deadline**: Дедлайн (опционально, формат ISO 8601)

    Только пользователи с ролью customer могут создавать задачи.
    Заказчиком автоматически становится текущий пользователь.
    """
    try:
        return TaskService.create_task(
            task_text=request.task_text,
            description=request.description,
            priority=request.priority,
            deadline=request.deadline,
            current_user=current_user
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
        task_id: int,
        current_user: dict = Depends(get_current_user)
):
    """
    Получить информацию о конкретной задаче.

    Требует:
    - **task_id**: ID задачи в пути URL

    Права доступа:
    - Заказчик может видеть любую свою задачу
    - Исполнитель может видеть только назначенные ему задачи
    - Admin может видеть все задачи
    """
    try:
        return TaskService.get_task(task_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
        task_id: int,
        request: TaskUpdate,
        current_user: dict = Depends(get_current_user)
):
    """
    Обновить задачу.

    Требует:
    - **task_id**: ID задачи в пути URL

    Поля, которые можно обновить:
    - **task_text**: Новый текст задачи
    - **description**: Новое описание
    - **priority**: Новый приоритет
    - **deadline**: Новый дедлайн
    - **status**: Новый статус
    - **executor_id**: ID исполнителя

    Права доступа:
    - Заказчик может обновить только свои задачи
    - Admin может обновить любую задачу
    """
    try:
        return TaskService.update_task(
            task_id,
            request.model_dump(exclude_unset=True),
            current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{task_id}/assign", response_model=TaskResponse)
def assign_task(
        task_id: int,
        executor_id: int,
        current_user: dict = Depends(get_current_user)
):
    """
    Назначить задачу исполнителю.

    Требует:
    - **task_id**: ID задачи в пути URL
    - **executor_id**: ID исполнителя (в параметре запроса)

    Права доступа:
    - Может назначить только заказчик этой задачи или admin

    Пример:
    - POST /api/v1/tasks/42/assign?executor_id=5
    """
    try:
        return TaskService.assign_task(task_id, executor_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
        task_id: int,
        current_user: dict = Depends(get_current_user)
):
    """
    Отметить задачу как выполненную.

    Требует:
    - **task_id**: ID задачи в пути URL

    Права доступа:
    - Может отметить только исполнитель этой задачи или admin

    После отметки статус становится **completed**.
    """
    try:
        return TaskService.complete_task(task_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(
        task_id: int,
        current_user: dict = Depends(get_current_user)
):
    """
    Отменить задачу.

    Требует:
    - **task_id**: ID задачи в пути URL

    Права доступа:
    - Может отменить только заказчик этой задачи или admin

    После отмены статус становится **cancelled**.
    """
    try:
        return TaskService.cancel_task(task_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
```

### Разбор контроллера `GET /tasks`

```python
@router.get("", response_model=TaskListResponse)
def get_tasks(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        customer_id: Optional[int] = None,
        executor_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
        current_user: dict = Depends(get_current_user)
):
```

- **`status`, `priority` и т.д.** — это параметры строки запроса (query parameters).
- **`current_user`** — автоматически получается из токена в заголовке.

```python
    try:
        return TaskService.get_tasks(
            status=status,
            priority=priority,
            ...
            current_user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- Вызываем сервис, передавая все параметры.
- Если возникла ошибка — возвращаем HTTP ошибку с нужным кодом.

## Подключение маршрутов (Router) к приложению

Наконец, создайте файл `src/api/v1/router.py`:

```python
from fastapi import APIRouter

from api.v1.auth import router as auth_router
from api.v1.users import router as users_router
from api.v1.tasks import router as tasks_router

api_router = APIRouter(prefix="/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(tasks_router)
```

И в `src/main.py`:

```python
from fastapi import FastAPI
from api.v1.router import api_router

app = FastAPI(
    title="Business Todo API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.include_router(api_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

Теперь все маршруты автоматически подключены:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/users/me`
- `GET /api/v1/tasks`
- `POST /api/v1/tasks`
- И так далее...

## Тестирование контроллеров с Postman

Вот пример, как тестировать API:

**1. Регистрация:**

```
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securepass123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "customer"
}

Response:
{
  "accessToken": "eyJ0eXAiOiJKV1QiLC...",
  "refreshToken": "eyJ0eXAiOiJKV1QiLC...",
  "expiresIn": 900,
  "user": { ... }
}
```

**2. Получение профиля:**

```
GET /api/v1/users/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLC...

Response:
{
  "user_id": 1,
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "customer",
  "status": "active"
}
```

**3. Создание задачи:**

```
POST /api/v1/tasks
Authorization: Bearer eyJ0eXAiOiJKV1QiLC...
Content-Type: application/json

{
  "task_text": "Купить продукты",
  "priority": "high",
  "deadline": "2025-01-20T18:00:00"
}

Response:
{
  "task_id": 1,
  "task_text": "Купить продукты",
  "priority": "high",
  "status": "new",
  "customer_id": 1,
  ...
}
```

## Тестирование контроллеров

Тестирование — это проверка того, что ваши контроллеры работают правильно. Вместо того, чтобы вручную проверять каждый эндпоинт в Postman, вы пишете автоматические тесты, которые проверяют всё сами.

### Что такое unit-тесты?

Unit-тест — это маленький кусок кода, который проверяет, работает ли одна функция правильно. Например:

- Тест для `/login` проверит: "Если отправить верный email и пароль, вернулся ли access token?"
- Тест для `/tasks` проверит: "Если я не авторизован, вернётся ли ошибка 401?"

### Инструменты для тестирования

**pytest** — главный инструмент для тестирования Python кода. Это библиотека, которая:

- Находит все тесты (файлы, начинающиеся с `test_` или функции `test_...`).
- Запускает их.
- Показывает результаты.

**TestClient** от FastAPI — позволяет тестировать контроллеры без запуска реального сервера.

### Установка

```bash
pip install pytest pytest-asyncio httpx
```

### Структура тестов

Создайте папку `tests` в корне проекта, а в ней `test_auth.py`:

```
project/
├── src/
│   ├── main.py
│   ├── api/
│   └── ...
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Общая конфигурация для тестов
│   ├── test_auth.py         # Тесты для auth контроллера
│   ├── test_users.py        # Тесты для users контроллера
│   └── test_tasks.py        # Тесты для tasks контроллера
├── pytest.ini               # Конфиг pytest
└── ...
```

### Файл конфигурации pytest

Создайте `pytest.ini` в корне проекта:

```ini
[pytest]
pythonpath = ./src
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Общая конфигурация для тестов (conftest.py)

Создайте `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app


@pytest.fixture
def client():
    """
    Фикстура для тестирования API.
    Возвращает TestClient, который имитирует HTTP запросы без запуска сервера.
    """
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Фикстура с тестовыми данными пользователя"""
    return {
        "user_id": 1,
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password_hash": "hashed_password",
        "role": "customer",
        "status": "active",
        "created_at": "2025-01-01T00:00:00",
        "phone": None
    }


@pytest.fixture
def mock_task():
    """Фикстура с тестовыми данными задачи"""
    return {
        "task_id": 1,
        "task_text": "Test task",
        "description": "Test description",
        "customer_id": 1,
        "executor_id": None,
        "status": "new",
        "priority": "medium",
        "deadline": "2025-01-20T18:00:00",
        "completed_at": None,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    }
```

### Простой тест для контроллера

Создайте `tests/test_auth.py`:

```python
import pytest
from unittest.mock import patch
from fastapi import status


class TestAuthController:
    """Тесты для контроллера аутентификации"""

    @patch("services.auth_service.AuthService.login")
    def test_login_success(self, mock_login, client):
        """
        Тест: успешный вход в систему.
        Проверяем, что при верных credentials вернулась 200 и токены.
        """
        # Подготовка: мокируем сервис
        mock_login.return_value = {
            "accessToken": "test_access_token",
            "refreshToken": "test_refresh_token",
            "expiresIn": 900,
            "user": {
                "user_id": 1,
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "customer",
                "status": "active"
            }
        }

        # Действие: отправляем POST запрос
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )

        # Проверка: ожидаем код 200 и нужные поля
        assert response.status_code == status.HTTP_200_OK
        assert "accessToken" in response.json()
        assert "refreshToken" in response.json()
        assert response.json()["user"]["email"] == "test@example.com"

    @patch("services.auth_service.AuthService.login")
    def test_login_invalid_credentials(self, mock_login, client):
        """
        Тест: вход с неверными credentials.
        Проверяем, что вернулась ошибка 401.
        """
        # Подготовка: сервис выбрасывает исключение
        mock_login.side_effect = ValueError("Invalid credentials")

        # Действие: отправляем неверные данные
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )

        # Проверка: ожидаем ошибку 401
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("services.auth_service.AuthService.register")
    def test_register_success(self, mock_register, client):
        """
        Тест: успешная регистрация.
        Проверяем, что вернулась 201 (Created) и статус active.
        """
        mock_register.return_value = {
            "accessToken": "new_access_token",
            "refreshToken": "new_refresh_token",
            "expiresIn": 900,
            "user": {
                "user_id": 2,
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "role": "customer",
                "status": "active"
            }
        }

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123",
                "first_name": "New",
                "last_name": "User",
                "role": "customer"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["user"]["status"] == "active"

    @patch("services.auth_service.AuthService.register")
    def test_register_email_already_exists(self, mock_register, client):
        """
        Тест: регистрация с существующей почтой.
        Проверяем, что вернулась ошибка 400.
        """
        mock_register.side_effect = ValueError("Email already registered")

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "password": "securepass123",
                "first_name": "Test",
                "last_name": "User",
                "role": "customer"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
```

### Тест для контроллера задач

Создайте `tests/test_tasks.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi import status


class TestTasksController:
    """Тесты для контроллера задач"""

    @patch("api.dependencies.get_current_user")
    @patch("services.task_service.TaskService.get_tasks")
    def test_get_tasks_success(self, mock_get_tasks, mock_get_current_user, client):
        """
        Тест: получение списка задач.
        Проверяем, что вернулся список с нужной структурой.
        """
        # Подготовка
        mock_get_current_user.return_value = {
            "user_id": 1,
            "role": "customer",
            "status": "active"
        }

        mock_get_tasks.return_value = {
            "tasks": [
                {
                    "task_id": 1,
                    "task_text": "Buy groceries",
                    "priority": "high",
                    "status": "new",
                    "customer_id": 1,
                    "executor_id": None
                }
            ],
            "total": 1,
            "page": 1,
            "limit": 20
        }

        # Действие
        response = client.get(
            "/api/v1/tasks",
            headers={"Authorization": "Bearer test_token"}
        )

        # Проверка
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["task_text"] == "Buy groceries"

    @patch("api.dependencies.get_current_user")
    def test_get_tasks_unauthorized(self, mock_get_current_user, client):
        """
        Тест: попытка получить задачи без авторизации.
        Проверяем, что вернулась ошибка 403 или 401.
        """
        mock_get_current_user.side_effect = Exception("Invalid token")

        response = client.get(
            "/api/v1/tasks",
            headers={"Authorization": "Bearer invalid_token"}
        )

        # Может быть 401 или 403 в зависимости от реализации
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @patch("api.dependencies.get_current_user")
    @patch("services.task_service.TaskService.create_task")
    def test_create_task_success(self, mock_create_task, mock_get_current_user, client):
        """
        Тест: создание новой задачи.
        Проверяем, что вернулась 201 и данные новой задачи.
        """
        mock_get_current_user.return_value = {
            "user_id": 1,
            "role": "customer",
            "status": "active"
        }

        mock_create_task.return_value = {
            "task_id": 5,
            "task_text": "New task",
            "priority": "high",
            "status": "new",
            "customer_id": 1,
            "created_at": "2025-01-01T00:00:00"
        }

        response = client.post(
            "/api/v1/tasks",
            headers={"Authorization": "Bearer test_token"},
            json={
                "task_text": "New task",
                "priority": "high"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["task_id"] == 5
        assert response.json()["task_text"] == "New task"

    @patch("api.dependencies.get_current_user")
    @patch("services.task_service.TaskService.create_task")
    def test_create_task_permission_denied(self, mock_create_task, mock_get_current_user, client):
        """
        Тест: попытка создать задачу с недостаточными правами.
        Проверяем, что вернулась ошибка 403.
        """
        mock_get_current_user.return_value = {
            "user_id": 1,
            "role": "executor",  # Только customer может создавать!
            "status": "active"
        }

        mock_create_task.side_effect = PermissionError("Not enough permissions")

        response = client.post(
            "/api/v1/tasks",
            headers={"Authorization": "Bearer test_token"},
            json={
                "task_text": "New task",
                "priority": "high"
            }
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
```

### Как запускать тесты?

**Запустить все тесты:**

```bash
pytest
```

**Запустить тесты с подробным выводом:**

```bash
pytest -v
```

**Запустить только тесты конкретного файла:**

```bash
pytest tests/test_auth.py
```

**Запустить только один тест:**

```bash
pytest tests/test_auth.py::TestAuthController::test_login_success
```

**Запустить тесты и показать покрытие кода:**

```bash
pip install pytest-cov
pytest --cov=src --cov-report=html
```

Это создаст папку `htmlcov/index.html` с красивым отчётом о том, какой % кода покрыт тестами.

### Пример вывода тестов

```
$ pytest -v

tests/test_auth.py::TestAuthController::test_login_success PASSED                  [20%]
tests/test_auth.py::TestAuthController::test_login_invalid_credentials PASSED      [40%]
tests/test_auth.py::TestAuthController::test_register_success PASSED               [60%]
tests/test_auth.py::TestAuthController::test_register_email_already_exists PASSED  [80%]
tests/test_tasks.py::TestTasksController::test_get_tasks_success PASSED            [100%]

================================ 5 passed in 0.23s ================================
```

**Зелёные PASSED** — тесты прошли успешно!

Если тест **не прошёл**, вы увидите:

```
tests/test_auth.py::TestAuthController::test_login_success FAILED

def test_login_success(self, mock_login, client):
    ...
>   assert response.status_code == status.HTTP_200_OK
E   AssertionError: assert 500 == 200

tests/test_auth.py:123: AssertionError
```

Это означает, что вернулась ошибка **500**, а не **200**. Нужно найти, что не так.

### Что тестировать в контроллерах?

| Что проверять           | Пример                                                             |
| ----------------------- | ------------------------------------------------------------------ |
| **Успешный результат**  | POST /login с верными данными вернёт 200 и токены                  |
| **Ошибки валидации**    | POST /login без email вернёт 400                                   |
| **Ошибки авторизации**  | GET /tasks без токена вернёт 401                                   |
| **Ошибки прав доступа** | Executor не может создавать задачи (403)                           |
| **Ошибки от сервиса**   | Если сервис выбросил ошибку, контроллер вернёт правильный HTTP код |
| **Структура ответа**    | Ответ содержит все нужные поля                                     |

### Как понять, что пошло не так?

Когда тест падает, читайте вывод:

```
AssertionError: assert 401 == 200
```

Означает: "Я ожидал 200, но получил 401". Проверьте:

- Передали ли вы токен?
- Верный ли токен?
- Активен ли пользователь?

```
KeyError: 'accessToken'
```

Означает: "В ответе нет поля 'accessToken'". Проверьте:

- Возвращает ли контроллер правильный формат?
- Правильно ли сформирован ответ от сервиса?

## Ключевые принципы контроллеров

| Принцип                | Описание                                                               |
| ---------------------- | ---------------------------------------------------------------------- |
| **Валидация**          | FastAPI автоматически валидирует входные данные через Pydantic         |
| **Авторизация**        | Используйте `Depends(get_current_user)` для проверки токена            |
| **Правильные коды**    | Возвращайте правильные HTTP коды (200, 201, 400, 401, 403, 404 и т.д.) |
| **Документация**       | Пишите docstrings — FastAPI автоматически создаст Swagger документацию |
| **Обработка ошибок**   | Всегда ловите исключения и возвращайте понятные ошибки                 |
| **Минимальная логика** | Контроллер только принимает/возвращает данные, логика в сервисе        |
| **Тестирование**       | Пишите unit-тесты для каждого контроллера с помощью pytest             |
