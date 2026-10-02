"""Año lectivo, paso 3.7: lo que cuesta guardar, antes y despues de la guardia.

Ver `docs/funcionalidades/ANIO_LECTIVO.md`, "Medicion previa del paso 3.7".
Cada ruta pasa por la aplicacion real (ASGI) con una base simulada que cuenta
las conexiones que se piden al pool y las consultas que se mandan (sin contar
la preparacion de cada conexion). El usuario de la sesion se dobla: la
autenticacion cuesta lo mismo con o sin guardia y no se cuenta.

`ANTES` son las cifras medidas el 2026-10-02, antes de escribir la guardia.
La guardia, aceptada por el usuario ese dia, suma **una consulta** en cada
guardado y **ninguna conexion**: corre dentro de una conexion que el guardado
ya abre. `CON_GUARDIA` dice que rutas la tienen ya; las demas siguen igual.

Es el camino feliz de cada ruta: la base simulada responde lo minimo para que
llegue a guardar (una fila "comodin" que vale 1 en cualquier columna, y
respuestas puntuales donde hace falta). Fija conteos, no el SQL: el texto de
cada consulta lo fijan las caracterizaciones de cada modulo.
"""
import asyncio
import json
import urllib.parse

import pytest

from app.db import session

PROFESOR = {"id": 7, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}

# La consulta de la guardia empieza siempre asi (repositorio del año).
SQL_GUARDIA = "SELECT al.anio, al.estado FROM"


class Comodin:
    """Fila que responde a casi todo: indice o clave -> 1, verdadera."""

    def __getitem__(self, clave):
        return 1

    def get(self, clave, defecto=None):
        return 1

    def __bool__(self):
        return True

    def __len__(self):
        return 1

    def __contains__(self, clave):
        return True

    def __iter__(self):
        return iter(())


def _texto(sql):
    return " ".join(str(sql).split())


class Base:
    """Pool, conexiones y cursores simulados que cuentan lo que se pide."""

    def __init__(self, respuestas=(), anio=(2026, "activo")):
        self.conexiones = 0
        self.consultas = []
        self.commits = 0
        # La guardia ve, por defecto, el año de hoy: 2026 activo.
        self.respuestas = [(SQL_GUARDIA, anio, [])] + list(respuestas)

    # --- pool ---
    def getconn(self):
        self.conexiones += 1
        return ConexionFalsa(self)

    def putconn(self, conexion, close=False):
        pass


class ConexionFalsa:
    def __init__(self, base):
        self.base = base
        self.autocommit = False

    def cursor(self, *args, **kwargs):
        return CursorFalso(self.base)

    def commit(self):
        self.base.commits += 1

    def rollback(self):
        pass

    def close(self):
        pass


class CursorFalso:
    def __init__(self, base):
        self.base = base
        self._uno = Comodin()
        self._todos = []
        self.rowcount = 1
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        texto = _texto(sql)
        if texto == "PREPARACION":
            return
        self.base.consultas.append(texto)
        self._uno, self._todos = Comodin(), []
        for fragmento, uno, todos in self.base.respuestas:
            if fragmento in texto:
                self._uno, self._todos = uno, todos
                break

    def fetchone(self):
        return self._uno

    def fetchall(self):
        return list(self._todos)

    def close(self):
        pass


@pytest.fixture
def con_base(monkeypatch):
    from app.controllers import plan_de_clases_controller

    monkeypatch.setattr(
        session, "apply_session_setup", lambda cursor: cursor.execute("PREPARACION")
    )
    # Borrar la imagen del almacenamiento no es una consulta.
    monkeypatch.setattr(plan_de_clases_controller, "delete_file", lambda ruta: None)

    def usar(base):
        monkeypatch.setattr(session, "get_pool", lambda: base)
        return base

    return usar


def peticion(usuario, metodo, ruta, cuerpo=None, formulario=None):
    """Una peticion real contra la app con `usuario` en sesion. Devuelve el status."""
    from app.dependencies import get_current_user
    from app.main import app

    ruta, _, consulta = ruta.partition("?")
    if formulario is not None:
        crudo = urllib.parse.urlencode(formulario).encode()
        tipo = b"application/x-www-form-urlencoded"
    else:
        crudo = json.dumps(cuerpo).encode() if cuerpo is not None else b""
        tipo = b"application/json"
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": metodo,
        "scheme": "http",
        "path": ruta,
        "raw_path": ruta.encode(),
        "query_string": consulta.encode(),
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", tipo),
            (b"content-length", str(len(crudo)).encode()),
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    salida = {"status": None, "body": b""}

    async def receive():
        return {"type": "http.request", "body": crudo, "more_body": False}

    async def send(mensaje):
        if mensaje["type"] == "http.response.start":
            salida["status"] = mensaje["status"]
        elif mensaje["type"] == "http.response.body":
            salida["body"] += mensaje.get("body", b"")

    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        asyncio.run(app(scope, receive, send))
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    return salida["status"], json.loads(salida["body"].decode() or "null")


IMAGEN = [("SELECT imagen1, estado_revision", ("planes/x.png", "pendiente"), [])]

# nombre -> (metodo, ruta, cuerpo, formulario, respuestas)
RUTAS = {
    "POST /notas": (
        "POST", "/notas",
        {"estudiante_id": 3, "asignacion_id": 9, "nota": 4.0, "descripcion": "Taller"}, None, [],
    ),
    "POST /planilla/nota": (
        "POST", "/planilla/nota",
        {"estudiante_id": 3, "asignacion_id": 9, "nota": 4.0, "descripcion": "Taller", "periodo": 1},
        None, [],
    ),
    "DELETE /planilla/tipo": (
        "DELETE", "/planilla/tipo?asignacion_id=9&descripcion=Taller&periodo=1", None, None, [],
    ),
    "POST /asistencia": (
        "POST", "/asistencia",
        [{"estudiante_id": 3, "asignacion_id": 9, "fecha": "2026-09-30",
          "estado": "presente", "periodo": 3}],
        None, [],
    ),
    "POST /boletines/guardar": (
        "POST", "/boletines/guardar",
        {"estudiante_id": 3, "asignacion_id": 9, "periodo": 3, "definitiva": 4.0,
         "detalles": [{"nota": 4.0, "observacion": "ok"}]},
        None, [],
    ),
    "POST /observaciones": (
        "POST", "/observaciones",
        {"estudiante_id": 3, "asignacion_id": 9, "periodo": 3, "conductual": "Bien"}, None, [],
    ),
    "PUT /observador/{id}": ("PUT", "/observador/15", {"conductual": "Bien"}, None, []),
    "PUT /planeador-anual/{asignacion}/{periodo}": (
        "PUT", "/planeador-anual/9/3", [{"unidad_tematica": "U1", "fecha": "2026-10-30"}], None, [],
    ),
    "POST /plan-de-clases": (
        "POST", "/plan-de-clases", None,
        {"asignacion_id": "9", "fecha": "2026-10-05", "tema": "Fracciones"}, [],
    ),
    "DELETE /plan-de-clases/{id}/imagen": (
        "DELETE", "/plan-de-clases/20/imagen?slot=imagen1", None, None, IMAGEN,
    ),
    "PATCH /plan-de-clases/{id}/observaciones/{id}/vista": (
        "PATCH", "/plan-de-clases/20/observaciones/4/vista", None, None, [],
    ),
    "DELETE /admin/plan-de-clases/{id}/imagen": (
        "DELETE", "/admin/plan-de-clases/20/imagen?slot=imagen1", None, None, IMAGEN,
    ),
}

# (ruta, rol) -> (conexiones, consultas), medido el 2026-10-02 antes de la guardia.
ANTES = {
    ("POST /notas", "profesor"): (5, 6),
    ("POST /notas", "admin"): (4, 5),
    ("POST /planilla/nota", "profesor"): (2, 6),
    ("POST /planilla/nota", "admin"): (1, 5),
    ("DELETE /planilla/tipo", "profesor"): (2, 3),
    ("DELETE /planilla/tipo", "admin"): (1, 2),
    ("POST /asistencia", "profesor"): (3, 6),
    ("POST /asistencia", "admin"): (2, 5),
    ("POST /boletines/guardar", "profesor"): (3, 7),
    ("POST /boletines/guardar", "admin"): (2, 6),
    ("POST /observaciones", "profesor"): (3, 5),
    ("POST /observaciones", "admin"): (2, 4),
    ("PUT /observador/{id}", "profesor"): (1, 1),
    ("PUT /planeador-anual/{asignacion}/{periodo}", "profesor"): (2, 3),
    ("PUT /planeador-anual/{asignacion}/{periodo}", "admin"): (1, 2),
    ("POST /plan-de-clases", "profesor"): (2, 3),
    ("POST /plan-de-clases", "admin"): (1, 2),
    ("DELETE /plan-de-clases/{id}/imagen", "profesor"): (2, 3),
    ("DELETE /plan-de-clases/{id}/imagen", "admin"): (1, 2),
    ("PATCH /plan-de-clases/{id}/observaciones/{id}/vista", "profesor"): (2, 2),
    ("DELETE /admin/plan-de-clases/{id}/imagen", "admin"): (1, 2),
}

# Rutas que ya llevan la guardia. Paso 3.7a: las que usa el profesor (el
# borrado de imagen del admin comparte el guardado con la del profesor).
CON_GUARDIA = {
    "POST /notas",
    "POST /planilla/nota",
    "DELETE /planilla/tipo",
    "POST /asistencia",
    "POST /boletines/guardar",
    "POST /observaciones",
    "PUT /observador/{id}",
    "PUT /planeador-anual/{asignacion}/{periodo}",
    "POST /plan-de-clases",
    "DELETE /plan-de-clases/{id}/imagen",
    "PATCH /plan-de-clases/{id}/observaciones/{id}/vista",
    "DELETE /admin/plan-de-clases/{id}/imagen",
}

USUARIOS = {"profesor": PROFESOR, "admin": ADMIN}


@pytest.mark.parametrize(("ruta", "rol"), sorted(ANTES), ids=lambda v: str(v))
def test_la_guardia_suma_una_consulta_y_ninguna_conexion(con_base, ruta, rol):
    metodo, url, cuerpo, formulario, respuestas = RUTAS[ruta]
    base = con_base(Base(respuestas))

    status, _ = peticion(USUARIOS[rol], metodo, url, cuerpo, formulario)

    conexiones, consultas = ANTES[(ruta, rol)]
    extra = 1 if ruta in CON_GUARDIA else 0
    assert status in (200, 201)
    assert base.conexiones == conexiones
    assert len(base.consultas) == consultas + extra
    assert sum(SQL_GUARDIA in c for c in base.consultas) == extra
