from psycopg2 import pool
from databases.business_todo.src.core.config import settings

connection_pool = pool.SimpleConnectionPool(
    1, 10,
    host=settings.DB_HOST,
    database=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    port=settings.DB_PORT
)


def get_db_connection():
    return connection_pool.getconn()


def release_db_connection(conn):
    connection_pool.putconn(conn)
