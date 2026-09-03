"""Contrato del endpoint de salud usado por el monitoreo externo.

`GET /health` es la unica ruta publica ademas de `login`, y su valor operativo
depende de tres cosas que estas pruebas fijan:

1. distingue "la API vive y la base contesta" de "la base fallo", porque un
   monitor solo mira el status code;
2. no exige autenticacion, porque un monitor no puede iniciar sesion;
3. no filtra el detalle del fallo al cuerpo de la respuesta, porque el mensaje
   de psycopg2 revela DSN, host y nombres internos.

Como el resto de la suite, no requieren PostgreSQL: la capa de datos va con
dobles. La peticion HTTP se conduce por la interfaz ASGI real, no llamando a la
funcion de la ruta, porque el status code es justo lo que se quiere observar.
No se usa `TestClient` porque `httpx` no esta instalado.
"""

import asyncio
import inspect
import json

import pytest
from fastapi.routing import APIRoute
from psycopg2.pool import PoolError

from app.core import health as core_health
from app.globals import tenant_schema_var
from app.main import app
from app.routes import health as rutas_health


class CursorFalso:
    def __init__(self, fila=(1,)):
        self.fila = fila
        self.ejecutados = []
        self.cerrado = False

    def execute(self, sentencia, parametros=None):
        self.ejecutados.append((sentencia, parametros))

    def fetchone(self):
        return self.fila

    def close(self):
        self.cerrado = True


class ConexionFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.devuelta_al_pool = False
        self.tenant_al_conectar = None

    def cursor(self, cursor_factory=None):
        return self._cursor

    def close(self):
        self.devuelta_al_pool = True


@pytest.fixture
def base_de_datos(monkeypatch):
    """Sustituye la conexion real y deja observar cursor y conexion usados."""

    def instalar(fila=(1,), error=None):
        cursor = CursorFalso(fila=fila)
        conexion = ConexionFalsa(cursor)

        def fake_get_connection():
            if error is not None:
                raise error
            # El tenant ya debe estar fijado cuando se pide la conexion: es lo
            # que `get_connection()` exige de verdad.
            conexion.tenant_al_conectar = tenant_schema_var.get()
            return conexion

        monkeypatch.setattr(core_health, "get_connection", fake_get_connection)
        return cursor, conexion

    return instalar


def _peticion_asgi(aplicacion, metodo, ruta):
    """Ejecuta una peticion HTTP real contra la app y devuelve status y cuerpo."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": metodo,
        "scheme": "http",
        "path": ruta,
        "raw_path": ruta.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-length", b"0"),
        ],
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


# ---------------------------------------------------------------------------
# Frontera HTTP
# ---------------------------------------------------------------------------


def test_health_responde_200_cuando_la_base_contesta(base_de_datos):
    base_de_datos()

    estado, cuerpo = _peticion_asgi(app, "GET", "/health")

    assert estado == 200
    assert cuerpo == {"status": "ok", "database": "ok"}


def test_health_responde_503_cuando_el_pool_esta_agotado(base_de_datos):
    """El incidente ya documentado en produccion debe activar la alerta."""
    base_de_datos(error=PoolError("connection pool exhausted"))

    estado, cuerpo = _peticion_asgi(app, "GET", "/health")

    assert estado == 503
    assert cuerpo == {"status": "degraded", "database": "error"}


def test_health_responde_503_cuando_la_consulta_no_devuelve_fila(base_de_datos):
    base_de_datos(fila=None)

    estado, cuerpo = _peticion_asgi(app, "GET", "/health")

    assert estado == 503
    assert cuerpo == {"status": "degraded", "database": "error"}


def test_health_no_revela_el_detalle_del_error(base_de_datos):
    base_de_datos(error=PoolError("host=neon-secreto dbname=colegio user=admin"))

    _estado, cuerpo = _peticion_asgi(app, "GET", "/health")

    serializado = json.dumps(cuerpo)
    assert "neon-secreto" not in serializado
    assert "PoolError" not in serializado


def test_health_registra_el_detalle_en_el_log(base_de_datos, caplog):
    """El detalle no va al cuerpo, pero tampoco puede perderse."""
    base_de_datos(error=PoolError("host=neon-secreto"))

    with caplog.at_level("ERROR", logger="app.core.health"):
        _peticion_asgi(app, "GET", "/health")

    assert "neon-secreto" in caplog.text


# ---------------------------------------------------------------------------
# Contrato de la ruta
# ---------------------------------------------------------------------------


def _ruta_health():
    # Se inspecciona el router y no `app.routes`: desde FastAPI 0.137
    # `include_router` es perezoso y `app.routes` ya no contiene las rutas
    # incluidas, sino un envoltorio `_IncludedRouter` por router.
    rutas = [
        ruta
        for ruta in rutas_health.router.routes
        if isinstance(ruta, APIRoute) and ruta.path == "/health"
    ]
    assert len(rutas) == 1, "se espera exactamente una ruta /health"
    return rutas[0]


def test_health_es_publica_y_solo_get():
    """Un monitor no puede iniciar sesion: la ruta no admite dependencias."""
    ruta = _ruta_health()

    assert ruta.methods == {"GET"}
    assert ruta.dependant.dependencies == []
    assert rutas_health.router.dependencies == []


def test_health_se_ejecuta_de_forma_sincrona():
    """La consulta es bloqueante, asi que FastAPI debe sacarla del event loop."""
    assert not inspect.iscoroutinefunction(_ruta_health().endpoint)


# ---------------------------------------------------------------------------
# Contrato de `check_database`
# ---------------------------------------------------------------------------


def test_check_database_consulta_select_1_sobre_public(base_de_datos):
    cursor, conexion = base_de_datos()

    assert core_health.check_database() is True
    assert cursor.ejecutados == [("SELECT 1", None)]
    assert conexion.tenant_al_conectar == "public"


def test_check_database_devuelve_la_conexion_al_pool(base_de_datos):
    cursor, conexion = base_de_datos()

    core_health.check_database()

    assert cursor.cerrado is True
    assert conexion.devuelta_al_pool is True


def test_check_database_cierra_todo_aunque_la_consulta_falle(base_de_datos):
    """Una fuga aqui agotaria el pool justo cuando se quiere diagnosticarlo."""
    cursor, conexion = base_de_datos()

    def explotar(_sentencia, _parametros=None):
        raise RuntimeError("la base se cayo a mitad de la consulta")

    cursor.execute = explotar

    assert core_health.check_database() is False
    assert cursor.cerrado is True
    assert conexion.devuelta_al_pool is True


def test_check_database_restaura_el_tenant_anterior(base_de_datos):
    """No puede dejar `public` pegado en el contexto de la peticion."""
    base_de_datos()
    token = tenant_schema_var.set("tenant_colegio_9")
    try:
        core_health.check_database()
        assert tenant_schema_var.get() == "tenant_colegio_9"
    finally:
        tenant_schema_var.reset(token)


def test_check_database_restaura_el_tenant_aunque_falle(base_de_datos):
    base_de_datos(error=PoolError("connection pool exhausted"))
    token = tenant_schema_var.set("tenant_colegio_9")
    try:
        assert core_health.check_database() is False
        assert tenant_schema_var.get() == "tenant_colegio_9"
    finally:
        tenant_schema_var.reset(token)
