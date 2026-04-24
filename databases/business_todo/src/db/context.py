from contextlib import contextmanager
from psycopg2.extras import RealDictCursor

from databases.business_todo.src.db.connection import get_db_connection, release_db_connection


@contextmanager
def get_db_cursor():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        release_db_connection(conn)
