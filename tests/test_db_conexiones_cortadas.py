"""Conexiones que la base corta mientras esperan libres en el pool.

Neon duerme la base tras unos minutos sin consultas y, al dormirse, corta toda
conexion abierta. El pool de psycopg2 no se entera: las sigue guardando y
entregando como si sirvieran. Medido con este mismo doble el 2026-11-03,
antes del arreglo las 5 primeras peticiones tras despertar fallaban con
"server closed the connection unexpectedly", una por conexion cortada.

Se construye un `ThreadedConnectionPool` autentico con `psycopg2.connect`
sustituido: no hace falta PostgreSQL y se ejercita el descarte real del pool.
"""

import psycopg2
import pytest
from psycopg2 import extensions
from psycopg2.pool import ThreadedConnectionPool

from app.config import settings
from app.db import session
from app.globals import tenant_schema_var

TENANT = "tenant_colegio_1"
MINIMO = 5
MAXIMO = 10


class InfoFalsa:
    transaction_status = extensions.TRANSACTION_STATUS_IDLE


class CursorFalso:
    def __init__(self, conexion):
        self._conexion = conexion
        self.ejecutados = []

    def __enter__(self):
        return self

    def __exit__(self, *_excepcion):
        return False

    def execute(self, sentencia, parametros=None):
        if self._conexion.cortada:
            # Lo que hace psycopg2 al perder el servidor: marca la conexion
            # como rota (`closed = 2`) y lanza OperationalError.
            self._conexion.closed = 2
            raise psycopg2.OperationalError("server closed the connection unexpectedly")
        self.ejecutados.append(sentencia)


class ConexionFalsa:
    def __init__(self, cortada):
        self.cortada = cortada
        self.closed = 0
        self.rollbacks = 0
        self.info = InfoFalsa()
        self.cursores = []
        self._autocommit = True

    @property
    def autocommit(self):
        return self._autocommit

    @autocommit.setter
    def autocommit(self, valor):
        if self.closed:
            raise psycopg2.InterfaceError("connection already closed")
        self._autocommit = valor

    def cursor(self, cursor_factory=None):
        cursor = CursorFalso(self)
        self.cursores.append(cursor)
        return cursor

    def rollback(self):
        if self.closed:
            raise psycopg2.InterfaceError("connection already closed")
        self.rollbacks += 1

    def close(self):
        if not self.closed:
            self.closed = 1


class BaseFalsa:
    """Doble de `psycopg2.connect`: decide como salen las conexiones."""

    def __init__(self):
        self.creadas = []
        self.intentos_de_conectar = 0
        self.nuevas_salen_cortadas = False
        self.caida = False

    def connect(self, *_args, **_kwargs):
        self.intentos_de_conectar += 1
        if self.caida:
            raise psycopg2.OperationalError("could not connect to server")
        conexion = ConexionFalsa(cortada=self.nuevas_salen_cortadas)
        self.creadas.append(conexion)
        return conexion

    def dormirse(self):
        """Lo que hace Neon al dormirse: corta toda conexion abierta."""
        for conexion in self.creadas:
            conexion.cortada = True


@pytest.fixture(autouse=True)
def tenant_fijado():
    token = tenant_schema_var.set(TENANT)
    try:
        yield
    finally:
        tenant_schema_var.reset(token)


@pytest.fixture
def base(monkeypatch):
    base = BaseFalsa()
    monkeypatch.setattr(psycopg2, "connect", base.connect)
    monkeypatch.setattr(settings, "DB_POOL_MAX_CONNECTIONS", MAXIMO)
    return base


@pytest.fixture
def pool(base, monkeypatch):
    # Al crearse, el pool abre `MINIMO` conexiones y las deja libres: las que
    # Neon corta al dormirse.
    pool = ThreadedConnectionPool(minconn=MINIMO, maxconn=MAXIMO, dsn="dsn-falso")
    monkeypatch.setattr(session, "_pool", pool)
    return pool


def test_tras_dormirse_la_base_ninguna_peticion_falla(base, pool):
    base.dormirse()

    for _ in range(MINIMO + 2):
        session.get_connection().close()

    # Las cortadas se descartan y basta una sola conexion nueva: al devolverla
    # vuelve al pool y la reutilizan las peticiones siguientes.
    assert len(base.creadas) == MINIMO + 1
    assert all(conexion.closed for conexion in base.creadas[:MINIMO])


def test_la_conexion_entregada_es_nueva_y_tiene_el_tenant_fijado(base, pool):
    base.dormirse()

    conexion = session.get_connection()

    nueva = base.creadas[-1]
    assert conexion._connection is nueva
    assert nueva.closed == 0
    assert nueva.autocommit is False
    # Reintentar no puede saltarse la preparacion: la conexion que se entrega
    # tiene el search_path del tenant como cualquier otra.
    texto = str(nueva.cursores[0].ejecutados[0])
    assert "SET search_path TO" in texto
    assert TENANT in texto


def test_un_error_que_no_corta_la_conexion_no_se_reintenta(base, pool, monkeypatch):
    """Solo se reintenta lo que psycopg2 marca como conexion rota."""

    def falla(_cursor):
        raise psycopg2.ProgrammingError("error en la sentencia")

    monkeypatch.setattr(session, "apply_session_setup", falla)

    with pytest.raises(psycopg2.ProgrammingError):
        session.get_connection()

    # Una sola conexion tomada, revertida y devuelta: nada se descarta ni se
    # abre de nuevo.
    assert len(base.creadas) == MINIMO
    assert not any(conexion.closed for conexion in base.creadas)
    assert sum(conexion.rollbacks for conexion in base.creadas) == 1


def test_si_la_base_no_responde_falla_como_hoy(base, pool):
    base.dormirse()
    base.caida = True

    with pytest.raises(psycopg2.OperationalError, match="could not connect"):
        session.get_connection()

    # Descarta las cortadas y prueba a conectar una sola vez: abrir una
    # conexion nueva no se reintenta.
    assert base.intentos_de_conectar == MINIMO + 1


def test_si_hasta_las_nuevas_salen_cortadas_se_rinde(base, pool):
    """Una base que corta todo lo que se le abre no deja el hilo dando vueltas."""
    base.dormirse()
    base.nuevas_salen_cortadas = True

    with pytest.raises(psycopg2.OperationalError, match="server closed"):
        session.get_connection()

    # Como mucho `DB_POOL_MAX_CONNECTIONS + 1` intentos: las 5 cortadas del
    # pool y 6 nuevas.
    assert len(base.creadas) == MAXIMO + 1
    assert all(conexion.closed for conexion in base.creadas)
