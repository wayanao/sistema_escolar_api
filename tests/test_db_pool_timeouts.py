"""Timeouts y comportamiento del pool, fijados en la subcapa 1.5.

Tres bloques:

1. Compatibilidad con un endpoint agrupado. El `-pooler` de Neon es PgBouncer en
   modo transaccion y solo admite cinco parametros de arranque; cualquier otro
   hace fallar la conexion entera con "unsupported startup parameter in
   options". Un primer intento de esta subcapa envio los timeouts justamente
   ahi y rompio el arranque contra la base real. Estas pruebas son la guardia
   para que no vuelva a ocurrir.

2. Forma de la sentencia de timeouts. Se aplican con set_config(..., TRUE), que
   equivale a SET LOCAL: dura lo que dura la transaccion y no puede filtrarse a
   otro cliente cuando el endpoint agrupado recicla la conexion.

3. Medicion real del comportamiento del pool. Se sustituye psycopg2.connect por
   un doble, de modo que se construye un ThreadedConnectionPool autentico sin
   necesidad de PostgreSQL.
"""

from contextlib import contextmanager

import psycopg2
import pytest
from psycopg2 import extensions
from psycopg2.pool import PoolError, ThreadedConnectionPool

from app.config import Settings, settings
from app.db import session
from app.globals import tenant_schema_var
from app.main import MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER

# Los cinco parametros de arranque que PgBouncer sabe rastrear, mas los que
# psycopg2 resuelve del lado cliente y nunca envia al servidor.
PARAMETROS_TOLERADOS_POR_UN_ENDPOINT_AGRUPADO = {
    "minconn",
    "maxconn",
    "dsn",
    "connect_timeout",
    "client_encoding",
    "datestyle",
    "timezone",
    "standard_conforming_strings",
    "application_name",
}


class InfoFalsa:
    def __init__(self, transaction_status):
        self.transaction_status = transaction_status


class ConexionInerte:
    """Lo minimo que el pool de psycopg2 toca de una conexion.

    Incluye `info.transaction_status` porque putconn lo consulta para decidir si
    devuelve la conexion tal cual, la revierte o la descarta.
    """

    def __init__(self, transaction_status=extensions.TRANSACTION_STATUS_IDLE):
        self.closed = 0
        self.rollbacks = 0
        self.info = InfoFalsa(transaction_status)

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = 1


@pytest.fixture
def parametros_del_pool(monkeypatch):
    """Captura los kwargs con los que se construiria el pool."""
    recibidos = {}

    def fake_pool(**kwargs):
        recibidos.update(kwargs)
        return "pool"

    monkeypatch.setattr(session, "ThreadedConnectionPool", fake_pool)
    return recibidos


@pytest.fixture
def pool_real(monkeypatch):
    """Construye un ThreadedConnectionPool autentico con conexiones falsas."""

    def instalar(minconn=1, maxconn=2, transaction_status=extensions.TRANSACTION_STATUS_IDLE):
        creadas = []

        def fake_connect(*_args, **_kwargs):
            conexion = ConexionInerte(transaction_status)
            creadas.append(conexion)
            return conexion

        monkeypatch.setattr(psycopg2, "connect", fake_connect)
        return ThreadedConnectionPool(minconn=minconn, maxconn=maxconn, dsn="dsn-falso"), creadas

    return instalar


# --- Bloque 1: compatibilidad con un endpoint agrupado ---


def test_los_timeouts_de_servidor_no_viajan_en_el_paquete_de_arranque(parametros_del_pool):
    """Regresion del fallo real contra Neon pooled.

    Enviar statement_timeout en `options` hacia fallar _create_pool() entero con
    "unsupported startup parameter in options: statement_timeout", y con el la
    aplicacion no arrancaba.
    """
    session._create_pool()

    assert "options" not in parametros_del_pool
    for guc in ("statement_timeout", "lock_timeout", "idle_in_transaction_session_timeout"):
        assert guc not in str(parametros_del_pool)


def test_el_pool_solo_usa_parametros_que_un_endpoint_agrupado_tolera(parametros_del_pool):
    session._create_pool()

    assert set(parametros_del_pool) <= PARAMETROS_TOLERADOS_POR_UN_ENDPOINT_AGRUPADO


def test_connect_timeout_si_se_conserva_porque_lo_resuelve_el_cliente(parametros_del_pool, monkeypatch):
    """connect_timeout es de libpq: no forma parte del paquete de arranque.

    Por eso es el unico timeout compatible con endpoint agrupado y directo por
    igual, y no se elimino al corregir el fallo.
    """
    monkeypatch.setattr(settings, "DB_CONNECT_TIMEOUT_SECONDS", 10)

    session._create_pool()

    assert parametros_del_pool["connect_timeout"] == 10


def test_el_pool_no_recibe_connect_timeout_si_esta_en_cero(parametros_del_pool, monkeypatch):
    monkeypatch.setattr(settings, "DB_CONNECT_TIMEOUT_SECONDS", 0)

    session._create_pool()

    assert "connect_timeout" not in parametros_del_pool


def test_el_pool_respeta_el_tamano_configurado(parametros_del_pool, monkeypatch):
    monkeypatch.setattr(settings, "DB_POOL_MIN_CONNECTIONS", 2)
    monkeypatch.setattr(settings, "DB_POOL_MAX_CONNECTIONS", 12)

    session._create_pool()

    assert parametros_del_pool["minconn"] == 2
    assert parametros_del_pool["maxconn"] == 12
    assert parametros_del_pool["dsn"] == settings.DATABASE_URL


# --- Bloque 2: forma de la sentencia de timeouts ---


def test_la_sentencia_fija_los_tres_timeouts_con_valores_ligados(monkeypatch):
    monkeypatch.setattr(settings, "DB_STATEMENT_TIMEOUT_MS", 30000)
    monkeypatch.setattr(settings, "DB_LOCK_TIMEOUT_MS", 10000)
    monkeypatch.setattr(settings, "DB_IDLE_IN_TRANSACTION_TIMEOUT_MS", 60000)

    sentencia, parametros = session.build_timeout_statement()

    assert sentencia == (
        "SELECT set_config(%s, %s, TRUE), set_config(%s, %s, TRUE), set_config(%s, %s, TRUE)"
    )
    assert parametros == (
        "statement_timeout", "30000",
        "lock_timeout", "10000",
        "idle_in_transaction_session_timeout", "60000",
    )


def test_la_sentencia_es_local_a_la_transaccion(monkeypatch):
    """El tercer argumento en TRUE equivale a SET LOCAL.

    Es lo que hace seguro el ajuste detras de un endpoint agrupado en modo
    transaccion: al terminar la transaccion se revierte, asi que no puede
    filtrarse al siguiente cliente que reciba esa misma conexion.
    """
    sentencia, _ = session.build_timeout_statement()

    assert ", TRUE)" in sentencia
    assert "set_config" in sentencia


def test_un_timeout_en_cero_se_omite_en_vez_de_enviarse(monkeypatch):
    monkeypatch.setattr(settings, "DB_STATEMENT_TIMEOUT_MS", 0)
    monkeypatch.setattr(settings, "DB_LOCK_TIMEOUT_MS", 10000)
    monkeypatch.setattr(settings, "DB_IDLE_IN_TRANSACTION_TIMEOUT_MS", 0)

    sentencia, parametros = session.build_timeout_statement()

    assert sentencia == "SELECT set_config(%s, %s, TRUE)"
    assert parametros == ("lock_timeout", "10000")


def test_sin_ningun_timeout_no_se_ejecuta_nada(monkeypatch):
    monkeypatch.setattr(settings, "DB_STATEMENT_TIMEOUT_MS", 0)
    monkeypatch.setattr(settings, "DB_LOCK_TIMEOUT_MS", 0)
    monkeypatch.setattr(settings, "DB_IDLE_IN_TRANSACTION_TIMEOUT_MS", 0)

    assert session.build_timeout_statement() is None


# --- Bloque 3: los timeouts se aplican al tomar una conexion ---


class CursorFalso:
    def __init__(self):
        self.ejecutados = []

    def __enter__(self):
        return self

    def __exit__(self, *_excepcion):
        return False

    def execute(self, sentencia, parametros=None):
        self.ejecutados.append((sentencia, parametros))

    def close(self):
        pass


class ConexionFalsa:
    def __init__(self):
        self.autocommit = None
        self.cursores = []

    def cursor(self, cursor_factory=None):
        cursor = CursorFalso()
        self.cursores.append(cursor)
        return cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class PoolFalso:
    def __init__(self):
        self.conexion = ConexionFalsa()
        self.devueltas = []

    def getconn(self):
        return self.conexion

    def putconn(self, conexion, close=False):
        self.devueltas.append((conexion, close))


@contextmanager
def _tenant(valor="tenant_colegio_1"):
    token = tenant_schema_var.set(valor)
    try:
        yield
    finally:
        tenant_schema_var.reset(token)


def test_tomar_una_conexion_fija_el_tenant_y_los_timeouts_en_una_sola_ida(monkeypatch):
    """Las dos sentencias viajan juntas desde el 2026-09-24.

    Antes eran dos `execute`, o sea dos idas a la base. Medido contra la base
    real: preparar una conexion pasa de ~180 ms a ~121 ms, y eso lo paga cada
    conexion de toda la API. Lo que se ejecuta no cambia, ni su orden.
    """
    pool = PoolFalso()
    monkeypatch.setattr(session, "_pool", pool)

    with _tenant():
        session.get_connection()

    ejecutados = pool.conexion.cursores[0].ejecutados
    assert len(ejecutados) == 1

    sentencia, parametros = ejecutados[0]
    # La sentencia es un objeto compuesto de psycopg2 -el esquema viaja como
    # Identifier, nunca interpolado a mano-, asi que se inspecciona su texto.
    texto = str(sentencia)
    # El search_path va primero: fija el tenant antes que nada.
    assert texto.index("SET search_path TO") < texto.index("SELECT set_config")
    assert "statement_timeout" in parametros


def test_sin_timeouts_configurados_solo_se_fija_el_tenant(monkeypatch):
    pool = PoolFalso()
    monkeypatch.setattr(session, "_pool", pool)
    monkeypatch.setattr(settings, "DB_STATEMENT_TIMEOUT_MS", 0)
    monkeypatch.setattr(settings, "DB_LOCK_TIMEOUT_MS", 0)
    monkeypatch.setattr(settings, "DB_IDLE_IN_TRANSACTION_TIMEOUT_MS", 0)

    with _tenant():
        session.get_connection()

    assert len(pool.conexion.cursores[0].ejecutados) == 1


# --- Bloque 4: comportamiento medido del pool ---


def test_el_pool_agotado_falla_rapido_en_vez_de_esperar(pool_real):
    pool, _ = pool_real(minconn=1, maxconn=2)
    pool.getconn()
    pool.getconn()

    # No se bloquea esperando un hueco: lanza de inmediato. Es la diferencia
    # entre una peticion que falla y un worker colgado indefinidamente.
    with pytest.raises(PoolError, match="exhausted"):
        pool.getconn()


def test_devolver_una_conexion_permite_volver_a_tomarla(pool_real):
    pool, creadas = pool_real(minconn=1, maxconn=2)
    primera = pool.getconn()
    pool.getconn()

    pool.putconn(primera)
    reutilizada = pool.getconn()

    assert reutilizada is primera
    assert len(creadas) == 2


def test_el_pool_no_abre_mas_conexiones_que_el_maximo(pool_real):
    pool, creadas = pool_real(minconn=1, maxconn=3)

    for _ in range(3):
        pool.getconn()
    with pytest.raises(PoolError):
        pool.getconn()

    assert len(creadas) == 3


def test_el_pool_revierte_una_conexion_devuelta_con_transaccion_abierta(pool_real):
    pool, _ = pool_real(
        minconn=1, maxconn=2, transaction_status=extensions.TRANSACTION_STATUS_INTRANS
    )
    conexion = pool.getconn()

    pool.putconn(conexion)

    # Segunda red, independiente de la de get_cursor: aunque un llamador devuelva
    # la conexion a medio transaccionar, el pool la limpia antes de reutilizarla.
    assert conexion.rollbacks == 1


def test_el_pool_descarta_una_conexion_en_estado_desconocido(pool_real):
    pool, _ = pool_real(
        minconn=1, maxconn=2, transaction_status=extensions.TRANSACTION_STATUS_UNKNOWN
    )
    conexion = pool.getconn()

    pool.putconn(conexion)

    # Estado desconocido significa conexion perdida: se cierra, no se reutiliza.
    assert conexion.closed == 1


def test_cerrar_el_pool_cierra_todas_las_conexiones(pool_real):
    pool, creadas = pool_real(minconn=2, maxconn=2)

    pool.closeall()

    assert all(conexion.closed for conexion in creadas)


def test_el_pool_cierra_lo_que_pasa_del_minimo_en_cada_rafaga(pool_real):
    """Por que `DB_POOL_MIN_CONNECTIONS` no puede valer 1.

    psycopg2 solo guarda `minconn` conexiones libres y cierra las demas al
    devolverlas. Por eso no es solo la primera rafaga tras arrancar la que abre
    conexiones nuevas: es cada una. Medido el 2026-10-25, el panel del
    profesor abria 16 en cada apertura, a ~0,5 s cada una y en fila.
    """
    pool, creadas = pool_real(minconn=1, maxconn=10)

    for _ in range(3):
        rafaga = [pool.getconn() for _ in range(5)]
        for conexion in rafaga:
            pool.putconn(conexion)

    # La del arranque, mas cuatro nuevas en cada una de las tres rafagas.
    assert len(creadas) == 1 + 3 * 4
    assert sum(1 for conexion in creadas if conexion.closed) == 3 * 4


def test_el_minimo_por_defecto_cubre_una_rafaga_de_todos_los_hilos(pool_real):
    """Con el valor por defecto, una rafaga no abre ninguna conexion nueva.

    La rafaga habitual mas grande es una conexion por hilo con todos los hilos
    del servidor ocupados: `app/main.py` los limita a
    `DB_POOL_MAX_CONNECTIONS // 2`. Se mira el valor por defecto del codigo y
    no `settings`, que un `.env` local puede cambiar.
    """
    minimo = Settings.model_fields["DB_POOL_MIN_CONNECTIONS"].default
    maximo = Settings.model_fields["DB_POOL_MAX_CONNECTIONS"].default
    hilos = maximo // MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER
    pool, creadas = pool_real(minconn=minimo, maxconn=maximo)

    for _ in range(3):
        rafaga = [pool.getconn() for _ in range(hilos)]
        for conexion in rafaga:
            pool.putconn(conexion)

    # Solo las que el pool abre al crearse.
    assert len(creadas) == minimo
    assert not any(conexion.closed for conexion in creadas)


def test_get_pool_reutiliza_la_misma_instancia(monkeypatch):
    llamadas = []

    def fake_create():
        llamadas.append(1)
        return object()

    monkeypatch.setattr(session, "_pool", None)
    monkeypatch.setattr(session, "_create_pool", fake_create)

    primero = session.get_pool()
    segundo = session.get_pool()

    assert primero is segundo
    assert len(llamadas) == 1
