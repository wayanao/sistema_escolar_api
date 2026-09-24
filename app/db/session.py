from contextlib import contextmanager
from threading import Lock

import psycopg2
from psycopg2 import sql
from psycopg2.pool import ThreadedConnectionPool

from app.config import settings
from app.db.tenant import build_tenant_search_path_statement

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


def _timeouts_de_sesion() -> tuple[tuple[str, int], ...]:
    """Timeouts activos. Un valor de 0 se omite en vez de enviarse.

    Enviar 0 desactivaria el timeout de forma explicita y pisaria el valor por
    defecto del servidor; omitirlo lo respeta.
    """
    ajustes = (
        ("statement_timeout", settings.DB_STATEMENT_TIMEOUT_MS),
        ("lock_timeout", settings.DB_LOCK_TIMEOUT_MS),
        ("idle_in_transaction_session_timeout", settings.DB_IDLE_IN_TRANSACTION_TIMEOUT_MS),
    )
    return tuple((nombre, valor) for nombre, valor in ajustes if valor > 0)


def build_timeout_statement() -> tuple[str, tuple[str, ...]] | None:
    """Sentencia que fija los timeouts para la transaccion en curso.

    Usa set_config(nombre, valor, TRUE). El tercer argumento en TRUE equivale a
    SET LOCAL: el ajuste dura hasta que la transaccion termina y no puede
    filtrarse a otro cliente.

    Esto NO puede hacerse con el parametro `options` del arranque. Detras de un
    endpoint agrupado —el `-pooler` de Neon es PgBouncer en modo transaccion—
    solo se admiten cinco parametros de arranque, y cualquier otro hace fallar la
    conexion entera con "unsupported startup parameter in options". set_config
    viaja como una consulta normal, asi que funciona igual contra un endpoint
    agrupado que contra uno directo.

    Devuelve None si no hay ningun timeout configurado.
    """
    ajustes = _timeouts_de_sesion()
    if not ajustes:
        return None

    llamadas = ", ".join(["set_config(%s, %s, TRUE)"] * len(ajustes))
    parametros: list[str] = []
    for nombre, valor in ajustes:
        parametros.extend((nombre, str(valor)))

    return f"SELECT {llamadas}", tuple(parametros)


def apply_session_timeouts(cursor) -> None:
    sentencia = build_timeout_statement()
    if sentencia is None:
        return
    cursor.execute(*sentencia)


def apply_session_setup(cursor) -> str:
    """Deja la conexion lista para consultar en una sola ida a la base.

    El search_path y los timeouts viajaban en dos `execute` separados. Medido
    contra la base real el 2026-09-24: una ida y vuelta cuesta ~60 ms, y
    preparar una conexion costaba ~180 ms -tres idas, contando el BEGIN
    implicito de psycopg2-. Mandando las dos sentencias juntas baja a ~121 ms,
    y ese ahorro lo cobra **cada** conexion de toda la API.

    Lo que se ejecuta es identico y en el mismo orden: el search_path primero,
    porque fija el tenant antes que nada, y ahora ademas viaja en la misma
    sentencia, asi que ya no puede quedar una sin la otra.
    """
    sentencia_tenant, tenant_schema = build_tenant_search_path_statement()
    timeouts = build_timeout_statement()

    if timeouts is None:
        cursor.execute(sentencia_tenant)
        return tenant_schema

    timeouts_sql, timeouts_params = timeouts
    cursor.execute(
        sql.SQL("{}; {}").format(sentencia_tenant, sql.SQL(timeouts_sql)),
        timeouts_params,
    )
    return tenant_schema


def _create_pool() -> ThreadedConnectionPool:
    # Solo parametros que un endpoint agrupado acepta. connect_timeout es de
    # libpq y se resuelve en el cliente: nunca viaja en el paquete de arranque.
    parametros = {
        "minconn": settings.DB_POOL_MIN_CONNECTIONS,
        "maxconn": settings.DB_POOL_MAX_CONNECTIONS,
        "dsn": settings.DATABASE_URL,
    }

    if settings.DB_CONNECT_TIMEOUT_SECONDS > 0:
        parametros["connect_timeout"] = settings.DB_CONNECT_TIMEOUT_SECONDS

    return ThreadedConnectionPool(**parametros)


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
            apply_session_setup(cursor)
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
