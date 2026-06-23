from contextlib import contextmanager
from threading import Lock

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from app.config import settings
from app.db.tenant import set_tenant_search_path

_pool: ThreadedConnectionPool | None = None
_pool_lock = Lock()


class PooledConnection:
    def __init__(self, pool: ThreadedConnectionPool, connection):
        self._pool = pool
        self._connection = connection
        self._closed = False

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def close(self) -> None:
        if not self._closed:
            try:
                self._connection.rollback()
            except psycopg2.Error:
                self._pool.putconn(self._connection, close=True)
                self._closed = True
                pass
            else:
                self._pool.putconn(self._connection)
                self._closed = True

    def real_close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True


def _create_pool() -> ThreadedConnectionPool:
    return ThreadedConnectionPool(
        minconn=settings.DB_POOL_MIN_CONNECTIONS,
        maxconn=settings.DB_POOL_MAX_CONNECTIONS,
        dsn=settings.DATABASE_URL,
    )


def get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = _create_pool()
    return _pool


def get_connection() -> PooledConnection:
    pool = get_pool()
    connection = pool.getconn()
    try:
        connection.autocommit = False
        with connection.cursor() as cursor:
            set_tenant_search_path(cursor)
    except Exception:
        try:
            connection.rollback()
        except psycopg2.Error:
            pool.putconn(connection, close=True)
        else:
            pool.putconn(connection)
        raise
    return PooledConnection(pool, connection)


@contextmanager
def get_cursor(commit: bool = False, cursor_factory=None):
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=cursor_factory)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
