"""Contrato de propiedad de conexion, cursor, commit y rollback.

Estas pruebas fijan lo que la infraestructura de app/db/session.py garantiza hoy.
Usan un pool falso: no requieren PostgreSQL y no dependen del entorno.

La garantia central es que la conexion siempre vuelve al pool, incluso cuando el
bloque protegido lanza una excepcion. Las subcapas siguientes se apoyan en ella.
"""

import pytest

from app.db import session
from app.globals import tenant_schema_var

TENANT = "tenant_colegio_1"


class CursorFalso:
    def __init__(self):
        self.ejecutados = []
        self.cerrado = False

    def __enter__(self):
        return self

    def __exit__(self, *excepcion):
        self.close()
        return False

    def execute(self, sentencia, parametros=None):
        self.ejecutados.append(sentencia)

    def close(self):
        self.cerrado = True


class ConexionFalsa:
    def __init__(self):
        self.autocommit = None
        self.commits = 0
        self.rollbacks = 0
        self.cerrada_de_verdad = False
        self.cursores = []

    def cursor(self, cursor_factory=None):
        cursor = CursorFalso()
        self.cursores.append(cursor)
        return cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada_de_verdad = True


class PoolFalso:
    def __init__(self):
        self.conexion = ConexionFalsa()
        self.entregadas = 0
        self.devueltas = []

    def getconn(self):
        self.entregadas += 1
        return self.conexion

    def putconn(self, conexion, close=False):
        self.devueltas.append((conexion, close))


@pytest.fixture
def pool_falso(monkeypatch):
    pool = PoolFalso()
    monkeypatch.setattr(session, "_pool", pool)
    return pool


@pytest.fixture
def tenant_fijado():
    token = tenant_schema_var.set(TENANT)
    try:
        yield TENANT
    finally:
        tenant_schema_var.reset(token)


@pytest.fixture
def sin_tenant():
    token = tenant_schema_var.set(None)
    try:
        yield
    finally:
        tenant_schema_var.reset(token)


def test_get_connection_prepara_la_conexion_y_la_retiene(pool_falso, tenant_fijado):
    conexion = pool_falso.conexion

    session.get_connection()

    assert pool_falso.entregadas == 1
    assert pool_falso.devueltas == []
    assert conexion.autocommit is False
    assert len(conexion.cursores) == 1
    assert len(conexion.cursores[0].ejecutados) == 1
    assert conexion.cursores[0].cerrado is True


def test_get_connection_devuelve_la_conexion_si_falla_la_preparacion(pool_falso, sin_tenant):
    with pytest.raises(RuntimeError):
        session.get_connection()

    assert pool_falso.entregadas == 1
    assert pool_falso.devueltas == [(pool_falso.conexion, False)]
    assert pool_falso.conexion.rollbacks == 1


def test_close_devuelve_al_pool_sin_cerrar_la_conexion(pool_falso, tenant_fijado):
    conexion = session.get_connection()

    conexion.close()

    assert pool_falso.devueltas == [(pool_falso.conexion, False)]
    assert pool_falso.conexion.rollbacks == 1
    assert pool_falso.conexion.cerrada_de_verdad is False


def test_close_es_idempotente(pool_falso, tenant_fijado):
    conexion = session.get_connection()

    conexion.close()
    conexion.close()

    assert len(pool_falso.devueltas) == 1


def test_real_close_cierra_la_conexion_y_no_la_devuelve(pool_falso, tenant_fijado):
    conexion = session.get_connection()

    conexion.real_close()

    assert pool_falso.devueltas == []
    assert pool_falso.conexion.cerrada_de_verdad is True


def test_get_cursor_confirma_cuando_se_pide_commit(pool_falso, tenant_fijado):
    with session.get_cursor(commit=True) as cursor:
        cursor.execute("SELECT 1")

    assert pool_falso.conexion.commits == 1
    assert len(pool_falso.devueltas) == 1


def test_get_cursor_no_confirma_por_defecto(pool_falso, tenant_fijado):
    with session.get_cursor() as cursor:
        cursor.execute("SELECT 1")

    assert pool_falso.conexion.commits == 0
    assert len(pool_falso.devueltas) == 1


def test_get_cursor_devuelve_la_conexion_ante_excepcion(pool_falso, tenant_fijado):
    with pytest.raises(ValueError):
        with session.get_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO notas_detalle VALUES (1)")
            raise ValueError("fallo a mitad de la operacion")

    assert pool_falso.conexion.commits == 0
    assert pool_falso.conexion.rollbacks >= 1
    assert len(pool_falso.devueltas) == 1


def test_get_cursor_cierra_el_cursor_ante_excepcion(pool_falso, tenant_fijado):
    with pytest.raises(ValueError):
        with session.get_cursor():
            raise ValueError("fallo a mitad de la operacion")

    cursor_del_bloque = pool_falso.conexion.cursores[-1]
    assert cursor_del_bloque.cerrado is True
