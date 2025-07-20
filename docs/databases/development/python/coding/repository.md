# Разработка слоя репозиториев web-приложения

Вам необходимо вручную создать SQL-таблицы, отражающие структуру социальной сети GopherTalk. Ниже описаны таблицы, их поля и связи между ними.

1. **Таблица `users`** — хранит данные пользователей.
2. **Таблица `posts`** — хранит публикации пользователей. Поле `reply_to_id` указывает на другой пост, если это ответ.
3. **Таблица `likes`** — отображает лайки пользователей к постам.
4. **Таблица `views`** — отображает просмотры постов пользователями.

```mermaid
erDiagram
  users {
    BIGSERIAL id PK
    VARCHAR(30) user_name
    VARCHAR(30) first_name
    VARCHAR(30) last_name
    VARCHAR(72) password_hash
    SMALLINT status
    TIMESTAMP created_at
    TIMESTAMP updated_at
    TIMESTAMP deleted_at
  }

  posts {
    BIGSERIAL id PK
    VARCHAR(280) text
    BIGINT reply_to_id FK
    BIGINT user_id FK
    TIMESTAMP created_at
    TIMESTAMP deleted_at
  }

  likes {
    BIGINT user_id PK, FK
    BIGINT post_id PK, FK
    TIMESTAMP created_at
  }

  views {
    BIGINT user_id PK, FK
    BIGINT post_id PK, FK
    TIMESTAMP created_at
  }

  users ||--o{ posts : ""
  users ||--o{ likes : ""
  users ||--o{ views : ""

  posts ||--o{ likes : ""
  posts ||--o{ views : ""
  posts ||--o{ posts : ""

```

### Требования:

- Используйте типы данных и ограничения согласно описанию.
- Настройте первичные и внешние ключи.
- Создайте уникальный индекс по `user_name`, но только для не удалённых пользователей (`deleted_at IS NULL`).
- Убедитесь, что `status` может быть только `0` или `1`.

> Подсказка: после создания таблиц, проверьте схему с помощью ER-диаграммы, чтобы убедиться в корректности связей.

## Архитектура приложения: контроллеры, сервисы и репозитории

Когда приложение начинает расти, добавляется всё больше бизнес-логики, валидации, работы с базой данных — и код быстро превращается в нечитаемую "кашу". Чтобы этого избежать, используется **разделение ответственности** — принцип, при котором каждый компонент отвечает только за свою задачу.

В небольших веб-приложениях удобно придерживаться следующей архитектуры:

### 1. Контроллеры (controllers)

Контроллер — это слой, который принимает HTTP-запрос, обрабатывает его и возвращает ответ. Здесь происходит:

- чтение параметров из объектов `Request`, `Path`, `Query`, `Body` или `Depends` FastAPI;,
- вызов нужного метода сервиса,
- формирование ответа (через `Response`, `JSONResponse` или возврат словаря).

Контроллер не содержит бизнес-логики и не обращается напрямую к базе данных — он просто **управляет потоком данных**. Кроме того, на уровне контроллера решаются вопросы по разграничению доступа к ресурсам и фильтрации запросов.

### 2. Сервисы (services)

Сервис — это слой, где находится основная **бизнес-логика приложения**. Он:

- обрабатывает данные,
- проверяет условия (например, "пользователь уже существует"),
- вызывает репозиторий для доступа к базе.

Сервис ничего не знает про HTTP или FastAPI — он универсален и может использоваться как в HTTP-приложении, так и, например, в CLI-утилите или фоновом скрипте.

### 3. Репозитории (repositories)

Репозиторий — это слой, отвечающий за **доступ к данным**. Обычно здесь хранятся SQL-запросы.  
Сервис говорит: "дай мне пользователя по id", а репозиторий выполняет конкретный SQL-запрос и возвращает результат.

Такой подход позволяет:

- изолировать работу с базой,
- легче писать и запускать юнит-тесты,
- менять способ хранения данных (например, заменить PostgreSQL на MongoDB) с минимальными изменениями.

### Преимущества архитектуры:

- Код становится **чище, понятнее и масштабируемее**;
- Каждый слой можно **тестировать отдельно**;
- Упрощается командная разработка — каждый работает в своей зоне ответственности;
- Легче поддерживать и расширять приложение в будущем.

В соответсвии с архитектурой мы построим разработку следующим образом: сначала разработаем слой репозитория, затем слой сервисов и в конце слой контроллеров. Для каждого слоя напишем Вам будут предоставлены unit-тесты для проверки корректности разработки конкретного слоя.

## Разработка репозитория пользователей

На этом этапе мы реализуем слой работы с базой данных — **репозиторий пользователей**.  
Задача этого слоя — обеспечивать сохранение, получение, обновление и удаление данных пользователей без участия бизнес-логики или HTTP-контроллеров.

Репозиторий будет включать методы:

- добавления нового пользователя,
- получения всех пользователей с пагинацией,
- поиска пользователя по `id` и по `user_name`,
- обновления данных пользователя,
- мягкого удаления пользователя.

Мы начнем с самого простого метода — `create_user`, который сохраняет нового пользователя в таблице `users`.  
Затем реализуем остальные методы и подключим unit-тесты для проверки корректности.

В папке `src` проекта создайте папку `repositories`, а в ней файл `user_repository.py`. Поместите в него следующий код:

```python
from config.db import pool
from psycopg.rows import dict_row


def create_user(dto: dict) -> dict:
    query = """
        INSERT INTO users (user_name, first_name, last_name, password_hash)
        VALUES (%s, %s, %s, %s)
        RETURNING id, user_name, password_hash, status;
    """
    values = (
        dto["user_name"],
        dto["first_name"],
        dto["last_name"],
        dto["password_hash"],
    )

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, values)
            return cur.fetchone()
```

Этот код реализует метод `create_user`, который отвечает за добавление нового пользователя в базу данных.

### Пошаговый разбор

- Импорт подключения к базе данных:

  ```python
  from config.db import pool
  ```

  Здесь мы импортируем заранее настроенный пул соединений с PostgreSQL, созданный с помощью `psycopg_pool.ConnectionPool` в модуле `config.db`. Через этот пул мы получаем подключения к базе и повторно их используем — без лишнего overhead'а на открытие новых TCP-сессий.

- Импорт `dict_row` для словарной формы результата:

  ```python
  from psycopg.rows import dict_row
  ```

  `dict_row` — это специальный row factory, который говорит `psycopg` возвращать строки не в виде кортежей, а в виде словарей (`dict`). Это удобно и читабельно: вместо `row[0]` можно писать `row["user_name"]`.

- Определение функции `create_user`:

  ```python
  def create_user(dto: dict) -> dict:
  ```

  Функция принимает словарь `dto`, содержащий данные нового пользователя: `user_name`, `first_name`, `last_name`, `password_hash`.
  Тип возвращаемого значения — `dict`, то есть мы возвращаем строку из базы в виде словаря.

- SQL-запрос на вставку

  ```python
  query = """
    INSERT INTO users (user_name, first_name, last_name, password_hash)
    VALUES (%s, %s, %s, %s)
    RETURNING id, user_name, password_hash, status;
  """
  ```

  Это SQL-запрос, который вставляет нового пользователя в таблицу `users`, использует позиционные параметры `%s` — безопасный способ подстановки значений и сразу возвращает `id`, `user_name`, `password_hash`, `status` — это нужно, чтобы после создания пользователя отдать его данные в API.

  ::: details SQL-инъекции
  SQL-инъекция — это один из самых распространённых видов атак на базу данных.
  Она возникает, когда ввод пользователя напрямую вставляется в SQL-запрос без проверки и экранирования, что позволяет злоумышленнику изменить логику запроса.

  **Пример уязвимого кода:**

  ```python
  cur.execute(f"SELECT * FROM users WHERE user_name = '{user_input}'")
  ```

  Вместо ожидаемого безопасного значения, пользователь ввёл строку `' OR 1=1 --`.

  В результате итоговый SQL-запрос будет выглядеть так:

  ```sql
  SELECT * FROM users WHERE user_name = '' OR 1=1 --';
  ```

  Что здесь происходит:

  - `user_name = ''` — первое условие, оно просто проверяет, что имя пользователя пустое;

  - `OR 1=1` — логическое выражение, которое всегда истинно, то есть условие выполняется для всех пользователей;

  - `--` — начало SQL-комментария, всё, что идёт после него, игнорируется СУБД;

  - `';` — эта часть уже не исполняется, так как закомментирована.

  Этот запрос вернёт всех пользователей из базы, потому что `1=1` всегда истинно. Если такой запрос используется при входе в систему, злоумышленник может войти без пароля, просто потому что запрос "обманывает" проверку логина.

  Используя позиционные параметры, мы избегаем этой проблемы:

  ```python
  cur.execute("SELECT * FROM users WHERE user_name = %s", (user_input,))
  ```

  В случае использования позиционных параметров, даже если пользователь введёт `' OR 1=1 --`, это не приведёт к SQL-инъекции, потому что ввод не вставляется напрямую в текст SQL-запроса. Вместо этого он передаётся отдельно в виде значения, а не как часть кода, а на уровне драйвера PostgreSQL (`psycopg`) реализован механизм, который:

  - экранирует специальные символы,

  - оборачивает значение в кавычки при необходимости,

  - и гарантирует, что ввод будет интерпретироваться именно как строка, а не как SQL-операторы.

  Проще говоря, драйвер сам "разделяет" SQL-код и пользовательские данные, не давая последним повлиять на логику выполнения запроса.

  Поэтому даже вредоносная строка будет просто передана как обычное значение поля `user_name`, а не как часть SQL-запроса.

  :::

- Подготовка значений для запроса:

  ```python
  values = (
    dto["user_name"],
    dto["first_name"],
    dto["last_name"],
    dto["password_hash"],
  )
  ```

  Значения берутся из входного объекта `dto` и передаются в том порядке, в котором указаны в SQL-запросе.

- Выполнение запроса

  ```python
  with pool.connection() as conn:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, values)
        return cur.fetchone()
  ```

  `pool.connection()` берёт соединение из пула, `conn.cursor(row_factory=dict_row)` создаёт курсор, возвращающий строки как словари, `cur.execute(...)` выполняет SQL-запрос, а `cur.fetchone()` возвращает первую строку результата, то есть только что созданного пользователя.

  После выполнения запроса возвращается первая (и единственная) строка результата — то есть данные только что созданного пользователя.

Мы реализовали создание пользователя. Далее необходимо реализовать следующие функции работы с пользователями:

- `get_all_users` — получение списка всех пользователей с пагинацией;
- `get_user_by_id` — получение пользователя по его `id`;
- `get_user_by_username` — получение пользователя по его имени пользователя (`user_name`);
- `update_user` — обновление данных пользователя;
- `delete_user` — мягкое удаление пользователя.

Начнём с функции `get_all_users`.

```python
from config.db import pool
from psycopg.rows import dict_row

def create_user(dto: dict) -> dict:
    query = """
        INSERT INTO users (user_name, first_name, last_name, password_hash)
        VALUES (%s, %s, %s, %s)
        RETURNING id, user_name, password_hash, status;
    """
    values = (
        dto["user_name"],
        dto["first_name"],
        dto["last_name"],
        dto["password_hash"],
    )

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, values)
            return cur.fetchone()


def get_all_users(limit: int, offset: int) -> list[dict]:
    query = """
        SELECT id, user_name, first_name, last_name, status, created_at, updated_at
        FROM users
        WHERE deleted_at IS NULL
        OFFSET %s LIMIT %s;
    """
    params = (offset, limit)

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchall()
```

Обратите внимание, что метод принимает два параметра - `offset` и `limit`. Они необходимы для того, чтобы сделать пагинацию, то есть отдавать не всех пользователей сразу, а частями в рамках скользящего окна.

Перейдем к функциям `get_user_by_id` и `get_user_by_user_name`.

```python
from config.db import pool
from psycopg.rows import dict_row

def create_user(dto: dict) -> dict:
    query = """
        INSERT INTO users (user_name, first_name, last_name, password_hash)
        VALUES (%s, %s, %s, %s)
        RETURNING id, user_name, password_hash, status;
    """
    values = (
        dto["user_name"],
        dto["first_name"],
        dto["last_name"],
        dto["password_hash"],
    )

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, values)
            return cur.fetchone()


def get_all_users(limit: int, offset: int) -> list[dict]:
    query = """
        SELECT id, user_name, first_name, last_name, status, created_at, updated_at
        FROM users
        WHERE deleted_at IS NULL
        OFFSET %s LIMIT %s;
    """
    params = (offset, limit)

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchall()

def get_user_by_id(user_id: int) -> dict:
    query = """
        ...
    """
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, (user_id,))
            result = cur.fetchone()

            if result is None:
                raise ValueError("User not found")

            return result

def get_user_by_username(user_name: str) -> dict:
  query = """
      ...
  """
  with pool.connection() as conn:
      with conn.cursor(row_factory=dict_row) as cur:
          cur.execute(query, (user_name,))
          result = cur.fetchone()

          if result is None:
              raise ValueError("User not found")
          return result

```

> [!IMPORTANT] Задание
> Напишите самостоятельно SQL запросы для функций `get_user_by_id` и `get_user_by_user_name`. Для метода `get_user_by_id` необходимо вернуть поля `id`, `user_name`, `first_name`, `last_name`, `status`, `created_at`, `updated_at`, а для метода `get_user_by_user_name` - `id`, `user_name`, `password_hash`, `status`.

Рассмотрим функцию `update_user`

```python
def update_user(user_id: int, dto: dict) -> dict:
    fields = []
    values = []

    if "password_hash" in dto:
        fields.append("password_hash = %s")
        values.append(dto["password_hash"])
    if "user_name" in dto:
        fields.append("user_name = %s")
        values.append(dto["user_name"])
    if "first_name" in dto:
        fields.append("first_name = %s")
        values.append(dto["first_name"])
    if "last_name" in dto:
        fields.append("last_name = %s")
        values.append(dto["last_name"])

    if not fields:
        raise ValueError("No fields to update")

    fields.append("updated_at = NOW()")
    values.append(user_id)

    query = f"""
        UPDATE users
        SET {", ".join(fields)}
        WHERE id = %s AND deleted_at IS NULL
        RETURNING id, user_name, first_name, last_name, status, created_at, updated_at;
    """

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, values)
            result = cur.fetchone()

            if result is None:
                raise ValueError("User not found")

            return result
```

Эта функция предназначена для обновления данных пользователя в базе данных. Она принимает два аргумента:

- `id`: Идентификатор пользователя, которого необходимо обновить.
- `dto`: Объект, содержащий данные для обновления.

### Логика работы функции `update_user`

1. **Инициализация**:

   - Создаются два списка:
     - `fields` — содержит SQL-строки вида `column_name = %s`;
     - `values` — содержит значения, которые будут подставлены в SQL-запрос.
   - Переменная `user_id` передаётся отдельно в конце, для подстановки в `WHERE`.

2. **Проверка и сбор полей для обновления**:

   - Функция последовательно проверяет наличие полей в словаре `dto`.
   - Если поле присутствует, оно добавляется в `fields`, а его значение — в `values`.
   - Поддерживаются следующие поля:
     - `password_hash`
     - `user_name`
     - `first_name`
     - `last_name`

3. **Проверка на пустое обновление**:

   - Если в `dto` не оказалось ни одного обновляемого поля, выбрасывается исключение `ValueError("No fields to update")`.

4. **Добавление метки времени**:

   - В `fields` добавляется `updated_at = NOW()` — это системное поле, не требующее подстановки.

5. **Формирование SQL-запроса**:

   - Поля в `fields` объединяются через запятую.
   - Генерируется SQL-запрос вида:
     ```sql
     UPDATE users SET field1 = %s, field2 = %s, ..., updated_at = NOW()
     WHERE id = %s AND deleted_at IS NULL
     RETURNING id, user_name, first_name, last_name, status, created_at, updated_at;
     ```

6. **Добавление ID в параметры запроса**:

   - В `values` добавляется `user_id` как последний аргумент, который используется в `WHERE id = %s`.

7. **Выполнение запроса**:

   - Открывается соединение с базой данных из пула.
   - Выполняется SQL-запрос через `cursor.execute(...)` с подставленными значениями.
   - Используется `row_factory=dict_row` для возврата результата в виде словаря.

8. **Обработка результата**:

   - Если пользователь не найден (`fetchone()` вернул `None`), выбрасывается `ValueError("User not found")`.
   - В противном случае возвращается результат — обновлённый пользователь в виде словаря.

Последняя функция, которую мы реализуем в этом репозитории - это функция удаления пользователя `delete_user`.

```python
def delete_user(user_id: int) -> None:
    query = """
        ...
    """

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            if cur.rowcount == 0:
                raise ValueError("User not found")
```

Эта функция предназначена для "удаления" пользователя из базы данных. Фактически, это мягкое удаление (soft delete), когда запись не удаляется физически, а лишь помечается как удалённая.

> [!IMPORTANT] Задание
> Напишите SQL-запрос, который выполняет мягкое удаление пользователя, устанавливая значение `deleted_at` в текущее время для пользователя с указанным `id`.

## Тестирование репозитория пользователей

В корне проекта создайте файл `pytest.ini` со следующим содержимым:

```text
[pytest]
pythonpath = ./src
```

Также в корне проекта создайте папку `__tests__`, а в ней папку `repositories`. В папке `repositories` создайте файл `test_user_repository.py` и поместите в него код с unit-тестами:

::: details Unit-тесты user_repository

```python
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from repositories.user_repository import (
    create_user,
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    update_user,
    delete_user,
)

def normalize_sql(sql: str) -> str:
    return " ".join(sql.lower().split())

@pytest.fixture
def mock_conn():
    with patch("config.db.pool.connection") as mock_conn_context:
        yield mock_conn_context


def test_create_user_success(mock_conn):
    dto = {
        "user_name": "john",
        "first_name": "John",
        "last_name": "Doe",
        "password_hash": "password",
    }
    expected = {
        "id": 1,
        "user_name": "john",
        "password_hash": "password",
        "status": 1,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = expected
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    result = create_user(dto)

    assert result == expected

def test_create_user_error(mock_conn):
    dto = {
        "user_name": "john",
        "first_name": "John",
        "last_name": "Doe",
        "password_hash": "password",
    }

    fake_error = Exception("insert failed")

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = fake_error
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="insert failed"):
        create_user(dto)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    assert "insert into users" in sql_called
    assert "user_name" in sql_called
    assert "password_hash" in sql_called

    params = mock_cursor.execute.call_args[0][1]
    assert params == (
        dto["user_name"],
        dto["first_name"],
        dto["last_name"],
        dto["password_hash"],
    )

def test_get_all_users_success(mock_conn):
    now = datetime.now()
    expected = [{
        "id": 1,
        "user_name": "john",
        "first_name": "John",
        "last_name": "Doe",
        "status": 1,
        "created_at": now,
        "updated_at": now,
    }]

    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = expected
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    result = get_all_users(limit=10, offset=0)
    assert result == expected


def test_get_all_users_error(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("SQL error")
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="SQL error"):
        get_all_users(limit=100, offset=0)

    sql_called = mock_cursor.execute.call_args[0][0].lower()

    normalized_sql = normalize_sql(sql_called)
    assert "from users where deleted_at is null" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (0, 100)


def test_get_user_by_id_success(mock_conn):
    now = datetime.now()
    expected = {
        "user_name": "john",
        "first_name": "John",
        "last_name": "Doe",
        "status": 1,
        "created_at": now,
        "updated_at": now,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = expected
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    result = get_user_by_id(1)
    assert result == expected


def test_get_user_by_id_not_found(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(ValueError, match="User not found"):
        get_user_by_id(999)


def test_get_user_by_username_success(mock_conn):
    expected = {
        "id": 1,
        "user_name": "john",
        "password_hash": "password",
        "status": 1,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = expected
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    result = get_user_by_username("john")
    assert result == expected


def test_get_user_by_username_not_found(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(ValueError, match="User not found"):
        get_user_by_username("notfound")


def test_update_user_success(mock_conn):
    now = datetime.now()
    earlier = now - timedelta(hours=1)

    dto = {
        "user_name": "john_updated",
        "first_name": "John",
        "last_name": "Doe",
        "password_hash": "password",
    }

    expected = {
        "id": 1,
        "user_name": "john_updated",
        "first_name": "John",
        "last_name": "Doe",
        "status": 1,
        "created_at": earlier,
        "updated_at": now,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = expected
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    result = update_user(1, dto)
    assert result == expected


def test_update_user_no_fields(mock_conn):
    with pytest.raises(ValueError, match="No fields to update"):
        update_user(1, {})


def test_update_user_not_found(mock_conn):
    dto = {"user_name": "ghost"}

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(ValueError, match="User not found"):
        update_user(999, dto)


def test_delete_user_success(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    assert delete_user(1) is None


def test_delete_user_not_found(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(ValueError, match="User not found"):
        delete_user(2)

```

:::

После этого выполните команду

```bash
pytest -v
```

Если вы все сделали правильно, все тесты пройдены.

```bash
tests/repositories/test_user_repository.py::test_create_user_success PASSED                                                                         [  7%]
tests/repositories/test_user_repository.py::test_create_user_error PASSED                                                                           [ 15%]
tests/repositories/test_user_repository.py::test_get_all_users_success PASSED                                                                       [ 23%]
tests/repositories/test_user_repository.py::test_get_all_users_error PASSED                                                                         [ 30%]
tests/repositories/test_user_repository.py::test_get_user_by_id_success PASSED                                                                      [ 38%]
tests/repositories/test_user_repository.py::test_get_user_by_id_not_found PASSED                                                                    [ 46%]
tests/repositories/test_user_repository.py::test_get_user_by_username_success PASSED                                                                [ 53%]
tests/repositories/test_user_repository.py::test_get_user_by_username_not_found PASSED                                                              [ 61%]
tests/repositories/test_user_repository.py::test_update_user_success PASSED                                                                         [ 69%]
tests/repositories/test_user_repository.py::test_update_user_no_fields PASSED                                                                       [ 76%]
tests/repositories/test_user_repository.py::test_update_user_not_found PASSED                                                                       [ 84%]
tests/repositories/test_user_repository.py::test_delete_user_success PASSED                                                                         [ 92%]
tests/repositories/test_user_repository.py::test_delete_user_not_found PASSED                                                                       [100%]

=================================================================== 13 passed in 0.12s ====================================================================
```

## Разработка репозитория постов

На этом этапе мы реализуем **репозиторий постов** — слой, отвечающий за взаимодействие с таблицей `posts`, а также связанными с ней таблицами `likes`, `views` и вложенными ответами (реплаями).

Репозиторий постов будет включать следующие методы:

- создание нового поста (`create_post`);
- получение списка постов с фильтрацией и пагинацией (`get_all_posts`);
- получение одного поста по `id`, включая автора, количество лайков, просмотров и ответов (`get_post_by_id`);
- удаление поста владельцем (`delete_post`);
- отметка, что пользователь просмотрел пост (`view_post`);
- лайк/дизлайк поста (`like_post`, `dislike_post`).

Мы начнем с реализации функции `create_post`, затем последовательно опишем остальные. Все методы взаимодействуют с базой через SQL-запросы, используют подстановки для защиты от SQL-инъекций и возвращают данные в формате DTO.

Создайте файл `src/repositories/post_repository.py`, в него поместите следующий код:

```python
from config.db import pool
from psycopg.rows import dict_row


def create_post(dto: dict) -> dict:
    query = """
        ...
    """
    values = (
        dto["text"],
        dto["user_id"],
        dto.get("reply_to_id"),
    )

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, values)
            return cur.fetchone()

```

Пояснение:

- `dto` — словарь, содержащий данные нового поста (`text`, `user_id`, `reply_to_id`);

- SQL-запрос вставляет данные в таблицу posts;

- После вставки сразу возвращаются поля нового поста: `id`, `text`, `created_at`, `reply_to_id`.

> [!IMPORTANT] Задание
> В соответствии с пояснением напишите SQL запрос для добавления нового поста. Не забудьте использовать позиционные параметры для предотвращения SQL-инъекций

Функция `get_all_posts` возвращает список постов с расширенной информацией: количество лайков, просмотров, ответов, а также информацию о пользователе и отметках "нравится" и "просмотрено" от текущего пользователя.

```python
def get_all_posts(dto: dict) -> list[dict]:
    params = [dto["user_id"]]
    query = """
        WITH likes_count AS (
            SELECT post_id, COUNT(*) AS likes_count
            FROM likes GROUP BY post_id
        ),
        views_count AS (
            SELECT post_id, COUNT(*) AS views_count
            FROM views GROUP BY post_id
        ),
        replies_count AS (
            SELECT reply_to_id, COUNT(*) AS replies_count
            FROM posts WHERE reply_to_id IS NOT NULL GROUP BY reply_to_id
        )
        SELECT
            p.id, p.text, p.reply_to_id, p.created_at,
            u.id AS user_id, u.user_name, u.first_name, u.last_name,
            COALESCE(lc.likes_count, 0) AS likes_count,
            COALESCE(vc.views_count, 0) AS views_count,
            COALESCE(rc.replies_count, 0) AS replies_count,
            CASE WHEN l.user_id IS NOT NULL THEN true ELSE false END AS user_liked,
            CASE WHEN v.user_id IS NOT NULL THEN true ELSE false END AS user_viewed
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN likes_count lc ON p.id = lc.post_id
        LEFT JOIN views_count vc ON p.id = vc.post_id
        LEFT JOIN replies_count rc ON p.id = rc.reply_to_id
        LEFT JOIN likes l ON l.post_id = p.id AND l.user_id = %s
        LEFT JOIN views v ON v.post_id = p.id AND v.user_id = %s
        WHERE p.deleted_at IS NULL
    """

    if "search" in dto and dto["search"]:
        query += f" AND p.text ILIKE %s"
        params.append(f"%{dto['search']}%")

    if "owner_id" in dto and dto["owner_id"]:
        query += f" AND p.user_id = %s"
        params.append(dto["owner_id"])

    if "reply_to_id" in dto and dto["reply_to_id"]:
        query += f" AND p.reply_to_id = %s ORDER BY p.created_at ASC"
        params.append(dto["reply_to_id"])
    else:
        query += " AND p.reply_to_id IS NULL ORDER BY p.created_at DESC"

    query += " OFFSET %s LIMIT %s"
    params.extend([dto["offset"], dto["limit"]])

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        {
            "id": row["id"],
            "text": row["text"],
            "reply_to_id": row["reply_to_id"],
            "created_at": row["created_at"],
            "likes_count": row["likes_count"],
            "views_count": row["views_count"],
            "replies_count": row["replies_count"],
            "user_liked": row["user_liked"],
            "user_viewed": row["user_viewed"],
            "user": {
                "id": row["user_id"],
                "user_name": row["user_name"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
            },
        }
        for row in rows
    ]

```

Метод `get_all_posts` предназначен для получения списка публикаций с расширенной информацией:

- автор поста;

- количество лайков, просмотров, ответов;

- флаги, лайкнул и/или просматривал ли текущий пользователь этот пост.

#### Структура SQL-запроса

Запрос построен с использованием CTE (Common Table Expressions) и выглядит следующим образом:

```sql
WITH likes_count AS (...),
     views_count AS (...),
     replies_count AS (...)
SELECT ...
FROM posts ...
```

Рассмотрим все части по порядку.

#### 1. Подсчёт количества лайков к каждому посту

```sql
likes_count AS (
  SELECT post_id, COUNT(*) AS likes_count
  FROM likes
  GROUP BY post_id
)
```

Здесь из таблицы `likes` собирается информация о количестве лайков для каждого поста. Используется `GROUP BY post_id`, чтобы сгруппировать лайки по постам.

#### 2. Подсчёт количества просмотров

```sql
views_count AS (
  SELECT post_id, COUNT(*) AS views_count
  FROM views
  GROUP BY post_id
)
```

Аналогично первой CTE, но теперь считаются просмотры из таблицы `views`.

#### 3. Подсчёт количества ответов на каждый пост

```sql
replies_count AS (
  SELECT reply_to_id, COUNT(*) AS replies_count
  FROM posts
  WHERE reply_to_id IS NOT NULL
  GROUP BY reply_to_id
)
```

Здесь из самой таблицы `posts` выбираются те строки, где `reply_to_id IS NOT NULL`, то есть это ответы на другие посты. Считается, сколько таких ответов у каждого родительского поста.

#### 4. Основной запрос

```sql
SELECT
  p.id, p.text, p.reply_to_id, p.created_at,
  u.id AS user_id, u.user_name, u.first_name, u.last_name,
  COALESCE(lc.likes_count, 0) AS likes_count,
  COALESCE(vc.views_count, 0) AS views_count,
  COALESCE(rc.replies_count, 0) AS replies_count,
  CASE WHEN l.user_id IS NOT NULL THEN true ELSE false END AS user_liked,
  CASE WHEN v.user_id IS NOT NULL THEN true ELSE false END AS user_viewed
FROM posts p
JOIN users u ON p.user_id = u.id
LEFT JOIN likes_count lc ON p.id = lc.post_id
LEFT JOIN views_count vc ON p.id = vc.post_id
LEFT JOIN replies_count rc ON p.id = rc.reply_to_id
LEFT JOIN likes l ON l.post_id = p.id AND l.user_id = $1
LEFT JOIN views v ON v.post_id = p.id AND v.user_id = $1
WHERE p.deleted_at IS NULL
...
```

Что здесь происходит:

- `JOIN users` — соединение поста с его автором по `user_id`;

- `LEFT JOIN` с `likes_count`, `views_count`, `replies_count` — добавляются данные из CTE о количестве лайков, просмотров и ответов;

- `LEFT JOIN likes l` и `views v` — проверяется, поставил ли лайк или просмотр текущий пользователь (`$1` — его id). Эти поля используются в логических выражениях ниже;

- `CASE WHEN ... THEN true ELSE false` — определяет `user_liked` и `user_viewed`;

- `COALESCE(..., 0)` — если данных о лайках/просмотрах/ответах нет (например, никто не лайкал), подставляется `0`;

- `WHERE p.deleted_at IS NULL` — фильтрация: берутся только не удалённые посты.

#### 5. Дополнительные фильтры

**По тексту:**

```sql
if "search" in dto and dto["search"]:
    query += f" AND p.text ILIKE %s"
    params.append(f"%{dto['search']}%")
```

Если передана строка `search`, ищутся посты, в тексте которых есть соответствие.

**По пользователю (автору):**

```sql
if "owner_id" in dto and dto["owner_id"]:
    query += f" AND p.user_id = %s"
    params.append(dto["owner_id"])
```

Если передан `owner_id`, отбираются посты конкретного пользователя.

**По ответам:**

```sql
if "reply_to_id" in dto and dto["reply_to_id"]:
    query += f" AND p.reply_to_id = %s ORDER BY p.created_at ASC"
    params.append(dto["reply_to_id"])
else:
    query += " AND p.reply_to_id IS NULL ORDER BY p.created_at DESC"
```

Проверяется, являются ли посты ответами на другой пост (`reply_to_id`) или это корневые посты.

#### 6. Пагинация

```python
query += " OFFSET %s LIMIT %s"
params.extend([dto["offset"], dto["limit"]])
```

Реализуется механика "скользящего окна" — выбирается определённый диапазон постов.

#### 7. Возвращаемый результат

Результат собирается в виде массива постов. Каждый пост содержит:

- данные самого поста,

- данные автора (`user`),

- количество лайков, просмотров, ответов,

- флаги `user_liked`, `user_viewed`.

Далее рассмотрим реализацию функции `get_post_by_id`.

```python
def get_post_by_id(post_id: int, user_id: int) -> dict:
    query = """
        WITH likes_count AS (
            SELECT post_id, COUNT(*) AS likes_count
            FROM likes
            GROUP BY post_id
        ),
        views_count AS (
            SELECT post_id, COUNT(*) AS views_count
            FROM views
            GROUP BY post_id
        ),
        replies_count AS (
            SELECT reply_to_id, COUNT(*) AS replies_count
            FROM posts
            WHERE reply_to_id IS NOT NULL
            GROUP BY reply_to_id
        )
        SELECT
            p.id AS post_id,
            p.text,
            p.reply_to_id,
            p.created_at,
            u.id AS user_id,
            u.user_name,
            u.first_name,
            u.last_name,
            COALESCE(lc.likes_count, 0) AS likes_count,
            COALESCE(vc.views_count, 0) AS views_count,
            COALESCE(rc.replies_count, 0) AS replies_count,
            CASE WHEN l.user_id IS NOT NULL THEN true ELSE false END AS user_liked,
            CASE WHEN v.user_id IS NOT NULL THEN true ELSE false END AS user_viewed
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN likes_count lc ON p.id = lc.post_id
        LEFT JOIN views_count vc ON p.id = vc.post_id
        LEFT JOIN replies_count rc ON p.id = rc.reply_to_id
        LEFT JOIN likes l ON l.post_id = p.id AND l.user_id = %s
        LEFT JOIN views v ON v.post_id = p.id AND v.user_id = %s
        WHERE p.id = %s AND p.deleted_at IS NULL;
    """
    params = (user_id, user_id, post_id)

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            row = cur.fetchone()

            if row is None:
                raise ValueError("Post not found")

            return {
                "id": row["post_id"],
                "text": row["text"],
                "reply_to_id": row["reply_to_id"],
                "created_at": row["created_at"],
                "likes_count": row["likes_count"],
                "views_count": row["views_count"],
                "replies_count": row["replies_count"],
                "user_liked": row["user_liked"],
                "user_viewed": row["user_viewed"],
                "user": {
                    "id": row["user_id"],
                    "user_name": row["user_name"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                },
            }

```

Функция `get_post_by_id` используется для получения одного конкретного поста по его идентификатору. Она возвращает расширенную информацию по посту, включая лайки, просмотры, количество ответов и данные об авторе. Функция похожа на `get_all_posts`, за исключением некоторых отличий.

**Фильтрация по ID поста**

Вместо выборки множества записей, запрос ограничивается одним постом:

```sql
WHERE p.id = $2 AND p.deleted_at IS NULL
```

Первый параметр — это `user_id` (нужен для определения, лайкнул ли/просматривал ли пользователь пост),
второй — это ID самого поста, который ищется.

**Отсутствует пагинация**

Метод возвращает только один пост, поэтому нет `OFFSET` и `LIMIT`.

**Возвращаемое значение**

`get_post_by_id` возвращает один объект поста, а `get_all_posts` - массив.

**Обработка крайних случаев**

Если пост не найден, `get_post_by_id` выбрасывает исключение "Post not found", а `get_all_posts` возвращает пустой массив.

Перейдем к реализации метода `delete_post`.

```python
def delete_post(post_id: int, owner_id: int) -> None:
    query = """
        ...
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (post_id, owner_id))
            if cur.rowcount == 0:
                raise ValueError("Post not found or already deleted")
```

> [!IMPORTANT] Задание
> Реализуйте метод `delete_post`, который помечает пост как удалённый. SQL-запрос должен обновлять поле `deleted_at` текущим временем, работать только с постами, принадлежащими автору и исключать уже удалённые посты.

Теперь реализуем метод, который регистрирует факт просмотра поста пользователем. Каждый пользователь может просмотреть пост только один раз — повторные просмотры не записываются.

```python
from psycopg.errors import UniqueViolation

def view_post(post_id: int, user_id: int) -> None:
    query = """
        ...
    """
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (post_id, user_id))
                if cur.rowcount == 0:
                    raise ValueError("Post not found")
    except UniqueViolation as err:
        if "pk__views" in str(err):
            raise ValueError("Post already viewed") from err
        raise
```

> [!CAUTION] Внимание
> Обратите внимание на строку `if "pk__views" in str(err)`. Здесь `pk__views` - это имя первичного ключа у таблицы `views`. Подставьте свое, если у вас отличается.

> [!IMPORTANT] Задание
> Реализуйте метод `view_post`, который добавляет новую запись в таблицу `views`.

Теперь реализуем метод, который позволяет пользователю поставить лайк посту. Один пользователь может поставить лайк одному посту только один раз — повторные попытки должны вызывать ошибку.

```python
def like_post(post_id: int, user_id: int) -> None:
    query = """
        ...
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (post_id, user_id))
                if cur.rowcount == 0:
                    raise ValueError("Post not found")
    except UniqueViolation as err:
        if "pk__likes" in str(err):
            raise ValueError("Post already liked") from err
        raise
```

> [!CAUTION] Внимание
> Обратите внимание на строку `if "pk__likes" in str(err)`. Здесь `pk__likes` - это имя первичного ключа у таблицы `likes`. Подставьте свое, если у вас отличается.

> [!IMPORTANT] Задание
> Реализуйте метод `like_post`, который добавляет новую запись в таблицу `likes`.

Метод `dislike_post` позволяет пользователю убрать лайк с поста, если он его ранее поставил.

```python
def dislike_post(post_id: int, user_id: int) -> None:
    query = """
        ...
    """

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (post_id, user_id))
            if cur.rowcount == 0:
                raise ValueError("Post not found")
```

> [!IMPORTANT] Задание
> Реализуйте метод `dislike_post`, который удаляет запись из таблицы `likes`.

## Тестирование репозитория постов

В папке `__tests__/repositories` создайте файл `test_post_repository.py` и поместите в него код с unit-тестами:

::: details Unit-тесты postRepository

```python
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from psycopg.errors import UniqueViolation
from repositories.post_repository import (create_post, delete_post,
                                          dislike_post, get_all_posts,
                                          get_post_by_id, like_post, view_post)


def normalize_sql(sql: str) -> str:
    return " ".join(sql.lower().split())


@pytest.fixture
def mock_conn():
    with patch("config.db.pool.connection") as mock_conn_context:
        yield mock_conn_context



def test_create_post_success(mock_conn):
    dto = {
        "text": "Lorem ipsum dolor sit amet, consectetur adipiscing",
        "user_id": 1,
        "reply_to_id": None,
    }

    expected = {
        "id": 1,
        "text": dto["text"],
        "created_at": datetime.now(),
        "reply_to_id": None,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = expected
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    result = create_post(dto)

    assert result == expected

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "insert into posts" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (dto["text"], dto["user_id"], dto["reply_to_id"])


def test_create_post_error(mock_conn):
    dto = {
        "text": "Lorem ipsum dolor sit amet, consectetur adipiscing",
        "user_id": 1,
        "reply_to_id": None,
    }

    fake_error = Exception("insert failed")

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = fake_error
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="insert failed"):
        create_post(dto)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "insert into posts" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (dto["text"], dto["user_id"], dto["reply_to_id"])

def test_create_post_success(mock_conn):
    dto = {
        "text": "Lorem ipsum dolor sit amet, consectetur adipiscing",
        "user_id": 1,
        "reply_to_id": None,
    }

    expected = {
        "id": 1,
        "text": dto["text"],
        "created_at": datetime.now(),
        "reply_to_id": None,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = expected
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    result = create_post(dto)

    assert result == expected

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "insert into posts" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (dto["text"], dto["user_id"], dto["reply_to_id"])


def test_create_post_error(mock_conn):
    dto = {
        "text": "Lorem ipsum dolor sit amet, consectetur adipiscing",
        "user_id": 1,
        "reply_to_id": None,
    }

    fake_error = Exception("insert failed")

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = fake_error
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="insert failed"):
        create_post(dto)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "insert into posts" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (dto["text"], dto["user_id"], dto["reply_to_id"])


def test_get_all_posts_success(mock_conn):
    now = datetime(2025, 4, 24, 20, 55, 53, 21000)

    dto = {
        "user_id": 1,
        "owner_id": 0,
        "limit": 100,
        "offset": 0,
        "reply_to_id": 1,
        "search": "test",
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "id": 1,
            "text": "Post 1",
            "reply_to_id": None,
            "created_at": now,
            "likes_count": 10,
            "views_count": 100,
            "replies_count": 0,
            "user_liked": True,
            "user_viewed": True,
            "user_id": 1,
            "user_name": "username",
            "first_name": "first",
            "last_name": "last",
        },
        {
            "id": 2,
            "text": "Post 2",
            "reply_to_id": None,
            "created_at": now,
            "likes_count": 5,
            "views_count": 50,
            "replies_count": 2,
            "user_liked": False,
            "user_viewed": True,
            "user_id": 1,
            "user_name": "username",
            "first_name": "first",
            "last_name": "last",
        },
    ]
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    result = get_all_posts(dto)

    assert result == [
        {
            "id": 1,
            "text": "Post 1",
            "reply_to_id": None,
            "created_at": now,
            "likes_count": 10,
            "views_count": 100,
            "replies_count": 0,
            "user_liked": True,
            "user_viewed": True,
            "user": {
                "id": 1,
                "user_name": "username",
                "first_name": "first",
                "last_name": "last",
            },
        },
        {
            "id": 2,
            "text": "Post 2",
            "reply_to_id": None,
            "created_at": now,
            "likes_count": 5,
            "views_count": 50,
            "replies_count": 2,
            "user_liked": False,
            "user_viewed": True,
            "user": {
                "id": 1,
                "user_name": "username",
                "first_name": "first",
                "last_name": "last",
            },
        },
    ]

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized = normalize_sql(sql_called)
    assert "select" in normalized

    params = mock_cursor.execute.call_args[0][1]
    assert params[0] == dto["user_id"]


def test_get_all_posts_error(mock_conn):
    dto = {
        "user_id": 1,
        "owner_id": 0,
        "limit": 100,
        "offset": 0,
        "reply_to_id": 1,
        "search": "test",
    }

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("query failed")
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="query failed"):
        get_all_posts(dto)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized = normalize_sql(sql_called)
    assert "select" in normalized

    params = mock_cursor.execute.call_args[0][1]
    assert params[0] == dto["user_id"]


def test_get_post_by_id_success(mock_conn):
    user_id = 1
    post_id = 1
    now = datetime.now()

    row = {
        "post_id": post_id,
        "text": "Lorem ipsum dolor sit amet, consectetur adipiscing",
        "reply_to_id": None,
        "created_at": now,
        "user_id": user_id,
        "user_name": "username",
        "first_name": "first_name",
        "last_name": "last_name",
        "likes_count": 10,
        "views_count": 100,
        "replies_count": 0,
        "user_liked": True,
        "user_viewed": True,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = row
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    result = get_post_by_id(post_id, user_id)

    assert result == {
        "id": row["post_id"],
        "text": row["text"],
        "reply_to_id": row["reply_to_id"],
        "created_at": row["created_at"],
        "likes_count": row["likes_count"],
        "views_count": row["views_count"],
        "replies_count": row["replies_count"],
        "user_liked": row["user_liked"],
        "user_viewed": row["user_viewed"],
        "user": {
            "id": row["user_id"],
            "user_name": row["user_name"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
        },
    }

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    assert "select" in normalize_sql(sql_called)

    params = mock_cursor.execute.call_args[0][1]
    assert params == (user_id, user_id, post_id)


def test_get_post_by_id_not_found(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="Post not found"):
        get_post_by_id(999, 1)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    assert "select" in normalize_sql(sql_called)

    params = mock_cursor.execute.call_args[0][1]
    assert params == (1, 1, 999)

def test_delete_post_success(mock_conn):
    post_id = 1
    owner_id = 1

    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    assert delete_post(post_id, owner_id) is None

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "update posts set deleted_at = now()" in normalized_sql
    assert "where id =" in normalized_sql and "user_id =" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (post_id, owner_id)


def test_delete_post_not_found(mock_conn):
    post_id = 2
    owner_id = 1

    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="Post not found or already deleted"):
        delete_post(post_id, owner_id)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "update posts set deleted_at = now()" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (post_id, owner_id)

def test_view_post_success(mock_conn):
    post_id = 1
    user_id = 1

    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    assert view_post(post_id, user_id) is None

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "insert into views (post_id, user_id)" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (post_id, user_id)


def test_view_post_error_sql(mock_conn):
    post_id = 2
    user_id = 1

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("insert failed")
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="insert failed"):
        view_post(post_id, user_id)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "insert into views (post_id, user_id)" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (post_id, user_id)


def test_view_post_already_viewed(mock_conn):
    post_id = 3
    user_id = 1

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = UniqueViolation(
        'duplicate key value violates unique constraint "pk__views"'
    )
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(ValueError, match="Post already viewed"):
        view_post(post_id, user_id)


def test_like_post_success(mock_conn):
    post_id = 1
    user_id = 1

    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    assert like_post(post_id, user_id) is None

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "insert into likes (post_id, user_id)" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (post_id, user_id)


def test_like_post_error(mock_conn):
    post_id = 2
    user_id = 1

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("insert failed")
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="insert failed"):
        like_post(post_id, user_id)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "insert into likes (post_id, user_id)" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (post_id, user_id)


def test_like_post_already_liked(mock_conn):
    post_id = 3
    user_id = 1

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = UniqueViolation(
        'duplicate key value violates unique constraint "pk__likes"'
    )
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(ValueError, match="Post already liked"):
        like_post(post_id, user_id)

def test_dislike_post_success(mock_conn):
    post_id = 1
    user_id = 1

    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    assert dislike_post(post_id, user_id) is None

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "delete from likes where post_id = %s and user_id = %s" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (post_id, user_id)


def test_dislike_post_error(mock_conn):
    post_id = 2
    user_id = 1

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("delete failed")
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="delete failed"):
        dislike_post(post_id, user_id)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "delete from likes where post_id = %s and user_id = %s" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (post_id, user_id)


def test_dislike_post_not_found(mock_conn):
    post_id = 3
    user_id = 1

    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with pytest.raises(Exception, match="Post not found"):
        dislike_post(post_id, user_id)

    sql_called = mock_cursor.execute.call_args[0][0].lower()
    normalized_sql = normalize_sql(sql_called)
    assert "delete from likes where post_id = %s and user_id = %s" in normalized_sql

    params = mock_cursor.execute.call_args[0][1]
    assert params == (post_id, user_id)
```

:::

Запустите тесты. Если вы все сделали правильно, все тесты пройдены.

```bash

tests/repositories/test_post_repository.py::test_create_post_success PASSED                                                                         [  3%]
tests/repositories/test_post_repository.py::test_create_post_error PASSED                                                                           [  6%]
tests/repositories/test_post_repository.py::test_get_all_posts_success PASSED                                                                       [ 10%]
tests/repositories/test_post_repository.py::test_get_all_posts_error PASSED                                                                         [ 13%]
tests/repositories/test_post_repository.py::test_get_post_by_id_success PASSED                                                                      [ 16%]
tests/repositories/test_post_repository.py::test_get_post_by_id_not_found PASSED                                                                    [ 20%]
tests/repositories/test_post_repository.py::test_delete_post_success PASSED                                                                         [ 23%]
tests/repositories/test_post_repository.py::test_delete_post_not_found PASSED                                                                       [ 26%]
tests/repositories/test_post_repository.py::test_view_post_success PASSED                                                                           [ 30%]
tests/repositories/test_post_repository.py::test_view_post_error_sql PASSED                                                                         [ 33%]
tests/repositories/test_post_repository.py::test_view_post_already_viewed PASSED                                                                    [ 36%]
tests/repositories/test_post_repository.py::test_like_post_success PASSED                                                                           [ 40%]
tests/repositories/test_post_repository.py::test_like_post_error PASSED                                                                             [ 43%]
tests/repositories/test_post_repository.py::test_like_post_already_liked PASSED                                                                     [ 46%]
tests/repositories/test_post_repository.py::test_dislike_post_success PASSED                                                                        [ 50%]
tests/repositories/test_post_repository.py::test_dislike_post_error PASSED                                                                          [ 53%]
tests/repositories/test_post_repository.py::test_dislike_post_not_found PASSED                                                                      [ 56%]
tests/repositories/test_user_repository.py::test_create_user_success PASSED                                                                         [ 60%]
tests/repositories/test_user_repository.py::test_create_user_error PASSED                                                                           [ 63%]
tests/repositories/test_user_repository.py::test_get_all_users_success PASSED                                                                       [ 66%]
tests/repositories/test_user_repository.py::test_get_all_users_error PASSED                                                                         [ 70%]
tests/repositories/test_user_repository.py::test_get_user_by_id_success PASSED                                                                      [ 73%]
tests/repositories/test_user_repository.py::test_get_user_by_id_not_found PASSED                                                                    [ 76%]
tests/repositories/test_user_repository.py::test_get_user_by_username_success PASSED                                                                [ 80%]
tests/repositories/test_user_repository.py::test_get_user_by_username_not_found PASSED                                                              [ 83%]
tests/repositories/test_user_repository.py::test_update_user_success PASSED                                                                         [ 86%]
tests/repositories/test_user_repository.py::test_update_user_no_fields PASSED                                                                       [ 90%]
tests/repositories/test_user_repository.py::test_update_user_not_found PASSED                                                                       [ 93%]
tests/repositories/test_user_repository.py::test_delete_user_success PASSED                                                                         [ 96%]
tests/repositories/test_user_repository.py::test_delete_user_not_found PASSED                                                                       [100%]
=================================================================== 30 passed in 0.10s ====================================================================
```

## Итог

Мы последовательно разработали два слоя доступа к данным — репозиторий пользователей и репозиторий постов, следуя архитектурному принципу разделения ответственности. Мы:

- Создали функции для основных операций с базой данных (создание, чтение, обновление, удаление).

- Реализовали SQL-запросы с использованием позиционных параметров, обеспечивающих защиту от SQL-инъекций.

- Поддержали гибкие фильтры, пагинацию и условия отбора данных (например, по `user_id`, `reply_to_id`, `text`).

- Обработали все возможные ошибки, включая ситуации "не найдено" и конфликты при повторных действиях (например, повторный лайк).

- Написали юнит-тесты, чтобы убедиться в корректности реализации всех функций.

Такой подход делает код читаемым, легко поддерживаемым и расширяемым. Теперь мы готовы перейти к разработке следующего слоя — функционального (сервисов), где будет реализована логика обработки данных и проверок перед их отправкой в репозитории.
