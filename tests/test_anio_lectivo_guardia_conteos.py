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

# Respuestas puntuales para las rutas de solo admin (paso 3.7b).
ASIGNACION = {
    "profesor_id": 7, "curso_id": 2, "materia_id": 10,
    "dia": "Lunes", "hora_inicio": "07:00", "hora_fin": "08:00",
}
NUEVA_ASIGNACION = [
    ("FROM asignaciones a JOIN profesor p", None, []),
    ("SELECT 1 FROM asignaciones WHERE profesor_id = %s AND curso_id", None, []),
    ("SELECT jornada FROM cursos WHERE id", ("Mañana",), []),
    ("SELECT nombre FROM materias WHERE id", ("MATEMATICAS",), []),
]
COLUMNAS_CONCEPTO = (
    "id nombre valor descripcion tipo_cobro fecha_limite dia_limite_mes dias_gracia "
    "mora_tipo mora_valor mes_inicial frecuencia_meses generacion_automatica activo "
    "created_at updated_at mes_final anio_lectivo_id"
).split()
CONCEPTO = {c: None for c in COLUMNAS_CONCEPTO} | {"id": 4, "nombre": "MENSUALIDAD", "valor": 0}
TABLAS = [(
    "FROM information_schema.tables", Comodin(),
    [(t,) for t in ("tipos_de_pagos", "tipos_pagos_cursos", "tipos_pagos_estudiantes")],
)]

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
    # --- Paso 3.7b: rutas de solo admin ---
    "POST /asignaciones": ("POST", "/asignaciones", ASIGNACION, None, NUEVA_ASIGNACION),
    "PUT /asignaciones/{id}": (
        "PUT", "/asignaciones/9", ASIGNACION, None,
        [("SELECT profesor_id, curso_id, materia_id, activo", (7, 2, 10, True, 9), [])]
        + NUEVA_ASIGNACION,
    ),
    "DELETE /asignaciones/{id}": ("DELETE", "/asignaciones/9", None, None, []),
    "DELETE /asignaciones/{profesor}/{curso}": ("DELETE", "/asignaciones/7/2", None, None, []),
    "PUT /cursos/{id}/orden-boletin": (
        "PUT", "/cursos/2/orden-boletin", {"materias": [{"materia_id": 10}, {"materia_id": 12}]},
        None, [("SELECT DISTINCT materia_id FROM asignaciones", Comodin(), [(10,), (12,)])],
    ),
    "PUT /cursos/{id}": (
        "PUT", "/cursos/2", {"nombre": "PRIMERO A", "jornada": "Mañana"}, None,
        [("SELECT id FROM cursos WHERE UPPER", None, [])],
    ),
    "PATCH /cursos/{id}/estado": ("PATCH", "/cursos/2/estado", {"estado": "inactivo"}, None, []),
    "POST /listas-seguimiento/{curso}/columnas": (
        "POST", "/listas-seguimiento/2/columnas", {"nombre": "Tarea"}, None,
        [("SELECT 1 FROM listas_seguimiento_columnas", None, [])],
    ),
    "POST /listas-seguimiento/columnas-en-todos-los-cursos": (
        "POST", "/listas-seguimiento/columnas-en-todos-los-cursos", {"nombre": "Tarea"}, None, [],
    ),
    "DELETE /listas-seguimiento/{curso}/columnas/{id}": (
        "DELETE", "/listas-seguimiento/2/columnas/5", None, None, [],
    ),
    "POST /listas-seguimiento/{curso}/marcas": (
        "POST", "/listas-seguimiento/2/marcas",
        [{"columna_id": 5, "estudiante_id": 3, "marcado": True}], None,
        [
            ("SELECT id, nombre FROM listas_seguimiento_columnas", Comodin(), [(5, "Tarea")]),
            ("SELECT id, nombre, apellido FROM estudiantes", Comodin(), [(3, "Ana", "Paz")]),
        ],
    ),
    "PATCH /admin/plan-de-clases/{id}/revision": (
        "PATCH", "/admin/plan-de-clases/20/revision", {"estado": "visto", "version": 1}, None, [],
    ),
    "POST /admin/plan-de-clases/{id}/observaciones": (
        "POST", "/admin/plan-de-clases/20/observaciones",
        {"observacion": "Revisar", "version": 1}, None, [],
    ),
    "PUT /tipos-pagos/{id}": (
        "PUT", "/tipos-pagos/4", {"nombre": "MENSUALIDAD", "valor": 0}, None,
        [("SELECT id FROM tipos_de_pagos WHERE LOWER(TRIM(nombre))", None, [])],
    ),
    "PUT /tipos-pagos/{id}/configuracion": (
        "PUT", "/tipos-pagos/4/configuracion", {"dias_gracia": 5}, None,
        [
            ("FROM information_schema.columns", Comodin(), [(c,) for c in COLUMNAS_CONCEPTO]),
            ("FROM tipos_de_pagos", CONCEPTO, []),
        ],
    ),
    "PUT /tipos-pagos/{id}/cursos": (
        "PUT", "/tipos-pagos/4/cursos", {"cursos": [{"curso_id": 2, "valor": 200000}]}, None,
        [("SELECT ARRAY(", {"cursos_de_otro_anio": []}, [])],
    ),
    "DELETE /tipos-pagos/{id}/cursos/{curso}": ("DELETE", "/tipos-pagos/4/cursos/2", None, None, []),
    "PUT /estudiantes/{id}/valores-pago-personalizados/{concepto}": (
        "PUT", "/estudiantes/3/valores-pago-personalizados/4", {"valor": 150000}, None, TABLAS,
    ),
    "DELETE /estudiantes/{id}/valores-pago-personalizados/{concepto}": (
        "DELETE", "/estudiantes/3/valores-pago-personalizados/4", None, None, TABLAS,
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
    # Paso 3.7b, solo admin.
    ("POST /asignaciones", "admin"): (1, 12),
    ("PUT /asignaciones/{id}", "admin"): (1, 11),
    ("DELETE /asignaciones/{id}", "admin"): (1, 2),
    ("DELETE /asignaciones/{profesor}/{curso}", "admin"): (1, 2),
    ("PUT /cursos/{id}/orden-boletin", "admin"): (1, 6),
    ("PUT /cursos/{id}", "admin"): (1, 2),
    ("PATCH /cursos/{id}/estado", "admin"): (1, 1),
    ("POST /listas-seguimiento/{curso}/columnas", "admin"): (1, 3),
    ("POST /listas-seguimiento/columnas-en-todos-los-cursos", "admin"): (1, 2),
    ("DELETE /listas-seguimiento/{curso}/columnas/{id}", "admin"): (1, 1),
    ("POST /listas-seguimiento/{curso}/marcas", "admin"): (1, 3),
    ("PATCH /admin/plan-de-clases/{id}/revision", "admin"): (1, 3),
    ("POST /admin/plan-de-clases/{id}/observaciones", "admin"): (1, 4),
    ("PUT /tipos-pagos/{id}", "admin"): (1, 2),
    ("PUT /tipos-pagos/{id}/configuracion", "admin"): (2, 4),
    ("PUT /tipos-pagos/{id}/cursos", "admin"): (1, 4),
    ("DELETE /tipos-pagos/{id}/cursos/{curso}", "admin"): (1, 1),
    ("PUT /estudiantes/{id}/valores-pago-personalizados/{concepto}", "admin"): (1, 8),
    ("DELETE /estudiantes/{id}/valores-pago-personalizados/{concepto}", "admin"): (1, 2),
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
    # Paso 3.7b: las de solo admin. "Columna en todos los cursos" no esta:
    # sin año pedido usa el activo, y con año la validacion que ya hacia trae
    # el estado, asi que su guardia no cuesta ninguna consulta.
    "POST /asignaciones",
    "PUT /asignaciones/{id}",
    "DELETE /asignaciones/{id}",
    "DELETE /asignaciones/{profesor}/{curso}",
    "PUT /cursos/{id}/orden-boletin",
    "PUT /cursos/{id}",
    "PATCH /cursos/{id}/estado",
    "POST /listas-seguimiento/{curso}/columnas",
    "DELETE /listas-seguimiento/{curso}/columnas/{id}",
    "POST /listas-seguimiento/{curso}/marcas",
    "PATCH /admin/plan-de-clases/{id}/revision",
    "POST /admin/plan-de-clases/{id}/observaciones",
    "PUT /tipos-pagos/{id}",
    "PUT /tipos-pagos/{id}/configuracion",
    "PUT /tipos-pagos/{id}/cursos",
    "DELETE /tipos-pagos/{id}/cursos/{curso}",
    "PUT /estudiantes/{id}/valores-pago-personalizados/{concepto}",
    "DELETE /estudiantes/{id}/valores-pago-personalizados/{concepto}",
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
