"""Fase 3 del año lectivo, lecturas por año. Paso 3.1: los años lectivos y la
regla del año pedido.

Ver `docs/funcionalidades/ANIO_LECTIVO.md`. Sin base de datos: dobles de
cursor, como el resto de pruebas del año lectivo. La ruta se conduce por la
aplicacion real (ASGI), como en `test_listas_seguimiento_routes.py`, porque
el codigo de estado y la proteccion solo se ven al pasar por HTTP.

Nada de lo que existia cambia en este paso: la ruta y las funciones son
nuevas. Lo que se fija aqui es:

- que años ve cada rol (decisiones 3 y 4);
- que sin año pedido no se gasta ninguna consulta, porque es el camino de
  todas las peticiones de hoy;
- que un profesor no puede pedir otro año y que un año inexistente se
  rechaza.
"""
import asyncio
import json
from contextlib import contextmanager

import pytest

from app.controllers import anios_lectivos_controller as controlador
from app.routes import anios_lectivos as rutas
from app.services.anio_lectivo import (
    AnioLectivoNoPermitidoError,
    listar_anios_visibles,
    resolver_anio_pedido,
)


ADMIN = {"id": 1, "rol": "admin"}
PROFESOR = {"id": 7, "rol": "profesor"}

# Guardados sin orden a proposito: el orden lo tiene que poner el SQL.
ANIOS = [
    (1, 2025, "cerrado"),
    (3, 2027, "preparacion"),
    (2, 2026, "activo"),
]

SQL_LISTAR = "SELECT id, anio, estado FROM anios_lectivos ORDER BY anio DESC"
SQL_ACTIVO = "SELECT id, anio, estado FROM anios_lectivos WHERE estado = 'activo'"
SQL_POR_ID = "SELECT id, anio, estado FROM anios_lectivos WHERE id = %s"


class CursorDeAnios:
    """Responde a las tres lecturas de `anios_lectivos` y anota cada una."""

    def __init__(self, anios=ANIOS):
        self.anios = list(anios)
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = " ".join(sql.split())
        self.consultas.append((sql, params))
        if sql == SQL_POR_ID:
            self._filas = [a for a in self.anios if a[0] == params[0]]
        elif sql == SQL_ACTIVO:
            self._filas = [a for a in self.anios if a[2] == "activo"]
        elif sql == SQL_LISTAR:
            self._filas = list(self.anios)
        else:
            raise AssertionError(f"consulta inesperada: {sql}")

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)


# ---------------------------------------------------------------------------
# Que años ve cada rol.
# ---------------------------------------------------------------------------


def test_el_admin_ve_todos_los_anios_con_una_consulta():
    cursor = CursorDeAnios()

    assert listar_anios_visibles(cursor, ADMIN) == ANIOS
    assert cursor.consultas == [(SQL_LISTAR, None)]


def test_el_profesor_ve_solo_el_anio_activo_con_una_consulta():
    cursor = CursorDeAnios()

    assert listar_anios_visibles(cursor, PROFESOR) == [(2, 2026, "activo")]
    assert cursor.consultas == [(SQL_ACTIVO, None)]


def test_sin_anio_activo_el_profesor_recibe_una_lista_vacia():
    cursor = CursorDeAnios([(1, 2025, "cerrado")])

    assert listar_anios_visibles(cursor, PROFESOR) == []


def test_un_rol_que_no_es_admin_ve_solo_el_activo():
    """Si mañana aparece otro rol, no hereda los años pasados por descuido."""
    cursor = CursorDeAnios()

    assert listar_anios_visibles(cursor, {"id": 9, "rol": "otro"}) == [(2, 2026, "activo")]


# ---------------------------------------------------------------------------
# La regla del año pedido, que usaran los listados de los pasos 3.2 a 3.5.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("usuario", [ADMIN, PROFESOR])
def test_sin_anio_pedido_no_se_consulta_nada(usuario):
    """Es el camino de todas las peticiones de hoy: no puede costar una ida mas."""
    cursor = CursorDeAnios()

    assert resolver_anio_pedido(cursor, None, usuario) is None
    assert cursor.consultas == []


@pytest.mark.parametrize("estado", ["preparacion", "activo", "cerrado", "reabierto"])
def test_el_admin_puede_mirar_un_anio_en_cualquier_estado(estado):
    cursor = CursorDeAnios([(5, 2030, estado)])

    assert resolver_anio_pedido(cursor, 5, ADMIN) == (5, 2030, estado)
    assert cursor.consultas == [(SQL_POR_ID, (5,))]


def test_el_profesor_puede_pedir_el_anio_activo():
    cursor = CursorDeAnios()

    assert resolver_anio_pedido(cursor, 2, PROFESOR) == (2, 2026, "activo")


@pytest.mark.parametrize("anio_id", [1, 3])
def test_el_profesor_no_puede_pedir_otro_anio(anio_id):
    cursor = CursorDeAnios()

    with pytest.raises(AnioLectivoNoPermitidoError) as error:
        resolver_anio_pedido(cursor, anio_id, PROFESOR)

    assert str(error.value) == "Solo se puede consultar el año lectivo activo."


@pytest.mark.parametrize("usuario", [ADMIN, PROFESOR])
def test_un_anio_que_no_existe_se_rechaza(usuario):
    cursor = CursorDeAnios()

    with pytest.raises(ValueError) as error:
        resolver_anio_pedido(cursor, 99, usuario)

    assert str(error.value) == "El año lectivo seleccionado no existe."


# ---------------------------------------------------------------------------
# El controlador: la forma de la respuesta.
# ---------------------------------------------------------------------------


@pytest.fixture
def cursor_del_controlador(monkeypatch):
    cursor = CursorDeAnios()

    @contextmanager
    def get_cursor_falso():
        yield cursor

    monkeypatch.setattr(controlador, "get_cursor", get_cursor_falso)
    return cursor


def test_la_respuesta_del_admin_trae_id_anio_y_estado(cursor_del_controlador):
    assert controlador.listar_anios_lectivos_controller(ADMIN) == [
        {"id": 1, "anio": 2025, "estado": "cerrado"},
        {"id": 3, "anio": 2027, "estado": "preparacion"},
        {"id": 2, "anio": 2026, "estado": "activo"},
    ]


def test_la_respuesta_del_profesor_trae_solo_el_activo(cursor_del_controlador):
    assert controlador.listar_anios_lectivos_controller(PROFESOR) == [
        {"id": 2, "anio": 2026, "estado": "activo"},
    ]


# ---------------------------------------------------------------------------
# La ruta, por HTTP.
# ---------------------------------------------------------------------------


def peticion_get(aplicacion, ruta):
    """Una peticion GET real contra la app. Devuelve (status, cuerpo)."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": ruta,
        "raw_path": ruta.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"testserver")],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    salida = {"status": None, "body": b""}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(mensaje):
        if mensaje["type"] == "http.response.start":
            salida["status"] = mensaje["status"]
        elif mensaje["type"] == "http.response.body":
            salida["body"] += mensaje.get("body", b"")

    asyncio.run(aplicacion(scope, receive, send))
    return salida["status"], json.loads(salida["body"].decode())


def test_la_proteccion_vive_en_el_router():
    """Asi una ruta nueva de años nace protegida."""
    from app.dependencies import get_current_user

    assert [d.dependency for d in rutas.router.dependencies] == [get_current_user]


def test_sin_sesion_la_ruta_responde_401():
    from app.main import app

    status, _ = peticion_get(app, "/anios-lectivos")

    assert status == 401


@pytest.mark.parametrize("usuario", [ADMIN, PROFESOR])
def test_admin_y_profesor_pueden_pedir_la_lista(monkeypatch, usuario):
    """La ruta solo pasa el usuario: que años ve lo decide el servicio."""
    from app.dependencies import get_current_user
    from app.main import app

    recibido = []

    def controlador_falso(current_user):
        recibido.append(current_user)
        return [{"id": 2, "anio": 2026, "estado": "activo"}]

    monkeypatch.setattr(rutas, "listar_anios_lectivos_controller", controlador_falso)
    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        status, cuerpo = peticion_get(app, "/anios-lectivos")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert status == 200
    assert cuerpo == [{"id": 2, "anio": 2026, "estado": "activo"}]
    assert recibido == [usuario]
