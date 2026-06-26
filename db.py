import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_db_connection(cursor_factory=RealDictCursor, options=None):
    """Create a database connection using DATABASE_URL from environment.

    Args:
        cursor_factory: psycopg2 cursor factory (default: RealDictCursor).
        options: Connection options string (e.g. statement timeout).

    Returns:
        A psycopg2 connection object.
    """
    database_url = os.getenv("DATABASE_URL")
    kwargs = {"cursor_factory": cursor_factory}
    if options:
        kwargs["options"] = options
    return psycopg2.connect(database_url, **kwargs)


@contextmanager
def db_connection(cursor_factory=RealDictCursor, options=None):
    """Context manager that yields (connection, cursor) and handles cleanup.

    Commits on success, rolls back on exception, always closes both.
    """
    conn = get_db_connection(cursor_factory=cursor_factory, options=options)
    cursor = conn.cursor()
    try:
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
