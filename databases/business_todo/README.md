Запуск:

cd databases/business_todo
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

Настроить .env

Создать БД:
CREATE DATABASE business_todo_db;

Выполнить query из db_init.sql

Находясь в Projects/books:
uvicorn databases.business_todo.src.main:app --reload --host 0.0.0.0 --port 8000

Тесты запускать из books/databases/business_todo
pytest -v

Технологии
FastAPI — веб-фреймворк
PostgreSQL + psycopg2 — база данных
python-jose + passlib — JWT и хеширование паролей
pytest + unittest.mock — тестирование
python-dotenv — управление конфигом
pydantic - валидация

![Swagger](docs\swagger.png)
![Schema](docs\schema.drawio)