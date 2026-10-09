"""Año lectivo, paso 3.7: la guardia de escritura.

Ver `docs/funcionalidades/ANIO_LECTIVO.md`, "La guardia de escritura". Nadie
escribe en un año cerrado (409); el profesor solo escribe en el activo (403 en
uno en preparacion o reabierto); el admin escribe en el activo, en el de
preparacion y en uno reabierto. Con el año activo, como hoy, todo sigue igual.
Paso 3.7a: las rutas que usa el profesor. Paso 3.7b: las de solo admin.

Tres bloques:

- la regla, sin base de datos;
- las tres lecturas del año (de una clase, de un plan, de una anotacion);
- cada ruta que guarda, por la aplicacion real (ASGI), con una base simulada
  cuyo año se elige: cerrado, en preparacion o reabierto. Se comprueba el
  codigo HTTP, el mensaje y que **no se escribio nada** (ninguna sentencia de
  escritura y ningun `commit`).

Lo que cuesta (una consulta mas, ninguna conexion) lo fija
`test_anio_lectivo_guardia_conteos.py`.
"""
import asyncio
import json
import urllib.parse

import pytest
from fastapi import HTTPException

from app.db import session
from app.repositories.anios_lectivos_repository import (
    leer_anio_de_anotacion,
    leer_anio_de_asignacion,
    leer_anio_de_concepto,
    leer_anio_de_plan,
    leer_anios_de_cursos,
)
from app.services.anio_lectivo import (
    MENSAJE_ANIO_CERRADO,
    MENSAJE_SOLO_ANIO_ACTIVO,
    AnioLectivoNoEditableError,
    exigir_anio_editable,
    exigir_anio_editable_para_admin,
)

PROFESOR = {"id": 7, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}
OTRO_ROL = {"id": 3, "rol": "acudiente"}

CERRADO = "El año lectivo 2026 está cerrado. Solo se puede consultar."
SOLO_ACTIVO = "Solo se pueden guardar cambios en el año lectivo activo."


# ---------------------------------------------------------------------------
# La regla.
# ---------------------------------------------------------------------------


def test_los_mensajes_son_los_del_documento():
    assert MENSAJE_ANIO_CERRADO.format(anio=2026) == CERRADO
    assert MENSAJE_SOLO_ANIO_ACTIVO == SOLO_ACTIVO


@pytest.mark.parametrize(
    ("estado", "usuario", "codigo"),
    [
        ("activo", ADMIN, None),
        ("activo", PROFESOR, None),
        ("preparacion", ADMIN, None),
        ("preparacion", PROFESOR, 403),
        ("reabierto", ADMIN, None),
        ("reabierto", PROFESOR, 403),
        ("cerrado", ADMIN, 409),
        ("cerrado", PROFESOR, 409),
        # Un rol que no es admin se trata como profesor.
        ("preparacion", OTRO_ROL, 403),
        # Un estado desconocido se trata como cerrado.
        ("archivado", ADMIN, 409),
    ],
)
def test_la_tabla_de_la_guardia(estado, usuario, codigo):
    if codigo is None:
        exigir_anio_editable((2026, estado), usuario)
        return
    with pytest.raises(AnioLectivoNoEditableError) as error:
        exigir_anio_editable((2026, estado), usuario)
    assert error.value.status_code == codigo
    assert error.value.detail == (CERRADO if codigo == 409 else SOLO_ACTIVO)


def test_el_mensaje_nombra_el_anio_cerrado():
    with pytest.raises(AnioLectivoNoEditableError) as error:
        exigir_anio_editable((2027, "cerrado"), ADMIN)
    assert error.value.detail == "El año lectivo 2027 está cerrado. Solo se puede consultar."


@pytest.mark.parametrize(
    ("estado", "codigo"),
    [("activo", None), ("preparacion", None), ("reabierto", None), ("cerrado", 409)],
)
def test_la_regla_de_las_rutas_de_solo_admin(estado, codigo):
    """Paso 3.7b: su router ya exige admin; solo un año cerrado lo frena."""
    if codigo is None:
        exigir_anio_editable_para_admin((2026, estado))
        return
    with pytest.raises(AnioLectivoNoEditableError) as error:
        exigir_anio_editable_para_admin((2026, estado))
    assert error.value.status_code == 409
    assert error.value.detail == CERRADO


def test_sin_fila_no_hace_nada():
    """Lo que no existe lo responde el guardado como siempre (404 o su error)."""
    exigir_anio_editable(None, PROFESOR)


def test_el_error_es_una_respuesta_http():
    """Asi atraviesa los `except HTTPException: raise` de las rutas."""
    assert issubclass(AnioLectivoNoEditableError, HTTPException)


# ---------------------------------------------------------------------------
# Las lecturas del año.
# ---------------------------------------------------------------------------


class CursorDeUnaFila:
    def __init__(self, fila):
        self.fila = fila
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.fila


@pytest.mark.parametrize(
    ("leer", "fragmentos"),
    [
        (
            leer_anio_de_asignacion,
            [
                "FROM asignaciones a",
                "JOIN cursos c ON c.id = a.curso_id",
                "JOIN anios_lectivos al ON al.id = c.anio_lectivo_id",
                "WHERE a.id = %s",
            ],
        ),
        (
            leer_anio_de_plan,
            [
                "FROM plan_de_clases p",
                "JOIN asignaciones a ON a.id = p.asignacion_id",
                "JOIN cursos c ON c.id = a.curso_id",
                "JOIN anios_lectivos al ON al.id = c.anio_lectivo_id",
                "WHERE p.id = %s",
            ],
        ),
        (
            leer_anio_de_anotacion,
            [
                "FROM observador_anotaciones o",
                "JOIN anios_lectivos al ON al.id = o.anio_lectivo_id",
                "WHERE o.id = %s",
            ],
        ),
    ],
    ids=["clase", "plan", "anotacion"],
)
def test_cada_lectura_es_una_consulta_por_id(leer, fragmentos):
    cursor = CursorDeUnaFila((2026, "cerrado"))

    assert leer(cursor, 15) == (2026, "cerrado")

    [(sql, params)] = cursor.consultas
    assert sql.startswith("SELECT al.anio, al.estado FROM")
    for fragmento in fragmentos:
        assert fragmento in sql
    assert params == (15,)


def test_el_anio_de_un_concepto_es_una_consulta_por_id():
    cursor = CursorDeUnaFila((2027, "preparacion"))

    assert leer_anio_de_concepto(cursor, 4) == (2027, "preparacion")

    [(sql, params)] = cursor.consultas
    assert sql.startswith("SELECT al.anio, al.estado FROM tipos_de_pagos tp")
    assert "JOIN anios_lectivos al ON al.id = tp.anio_lectivo_id" in sql
    assert "WHERE tp.id = %s" in sql
    assert params == (4,)


class CursorDeVariasFilas:
    def __init__(self, filas):
        self.filas = filas
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(sql.split()), params))

    def fetchall(self):
        return list(self.filas)


def test_los_anios_de_varios_cursos_son_una_sola_consulta():
    """Editar una clase mira su curso de antes y el nuevo: una consulta."""
    cursor = CursorDeVariasFilas([(2026, "cerrado"), {"anio": 2027, "estado": "activo"}])

    assert leer_anios_de_cursos(cursor, [2, 40]) == [(2026, "cerrado"), (2027, "activo")]

    [(sql, params)] = cursor.consultas
    assert sql.startswith("SELECT al.anio, al.estado FROM cursos c")
    assert "JOIN anios_lectivos al ON al.id = c.anio_lectivo_id" in sql
    assert "WHERE c.id = ANY(%s)" in sql
    assert params == ([2, 40],)


@pytest.mark.parametrize(
    "leer", [leer_anio_de_asignacion, leer_anio_de_plan, leer_anio_de_anotacion, leer_anio_de_concepto]
)
def test_cada_lectura_devuelve_tupla_tambien_con_cursor_de_diccionarios(leer):
    assert leer(CursorDeUnaFila({"anio": 2026, "estado": "activo"}), 15) == (2026, "activo")
    assert leer(CursorDeUnaFila(None), 15) is None


# ---------------------------------------------------------------------------
# Las rutas, por HTTP, con el año elegido.
# ---------------------------------------------------------------------------

SQL_GUARDIA = "SELECT al.anio, al.estado FROM"
ESCRITURAS = ("INSERT", "UPDATE", "DELETE")


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


class Base:
    """Pool simulado: la guardia ve `anio`; lo demas, lo minimo para guardar."""

    def __init__(self, anio, respuestas=()):
        self.consultas = []
        self.ids_de_la_guardia = []
        self.commits = 0
        # La lectura de varios cursos usa `fetchall`; las demas, `fetchone`.
        self.respuestas = [(SQL_GUARDIA, anio, [anio])] + list(respuestas)

    def getconn(self):
        return ConexionFalsa(self)

    def putconn(self, conexion, close=False):
        pass

    @property
    def escrituras(self):
        return [c for c in self.consultas if c.split()[0].upper() in ESCRITURAS]


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
        texto = " ".join(str(sql).split())
        if texto == "PREPARACION":
            return
        self.base.consultas.append(texto)
        if texto.startswith(SQL_GUARDIA):
            self.base.ids_de_la_guardia.append(params)
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
def con_anio(monkeypatch):
    from app.controllers import plan_de_clases_controller

    monkeypatch.setattr(
        session, "apply_session_setup", lambda cursor: cursor.execute("PREPARACION")
    )
    borrados = []
    monkeypatch.setattr(plan_de_clases_controller, "delete_file", borrados.append)

    def usar(anio, respuestas=()):
        base = Base(anio, respuestas)
        base.archivos_borrados = borrados
        monkeypatch.setattr(session, "get_pool", lambda: base)
        return base

    return usar


def peticion(usuario, metodo, ruta, cuerpo=None, formulario=None):
    """Una peticion real contra la app con `usuario` en sesion."""
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
CONTEXTO_VALOR_PERSONALIZADO = [
    ("SELECT tp.anio_lectivo_id, m.curso_id", (5, 2, 3), []),
] + TABLAS


def _anio_pedido(anio):
    """"Columna en todos los cursos" con `?anio_lectivo_id=5`: el año 5 es el
    de la prueba. Su guardia usa la validacion que ya hacia; no consulta mas."""
    return [("FROM anios_lectivos WHERE id = %s", (5,) + tuple(anio), [])]


# nombre -> (roles, metodo, ruta, cuerpo, formulario, respuestas)
RUTAS = {
    "POST /notas": (
        [PROFESOR, ADMIN], "POST", "/notas",
        {"estudiante_id": 3, "asignacion_id": 9, "nota": 4.0, "descripcion": "Taller"}, None, [],
    ),
    "POST /planilla/nota": (
        [PROFESOR, ADMIN], "POST", "/planilla/nota",
        {"estudiante_id": 3, "asignacion_id": 9, "nota": 4.0, "descripcion": "Taller", "periodo": 1},
        None, [],
    ),
    "DELETE /planilla/tipo": (
        [PROFESOR, ADMIN], "DELETE", "/planilla/tipo?asignacion_id=9&descripcion=Taller&periodo=1",
        None, None, [],
    ),
    "POST /asistencia": (
        [PROFESOR, ADMIN], "POST", "/asistencia",
        [{"estudiante_id": 3, "asignacion_id": 9, "fecha": "2026-09-30",
          "estado": "presente", "periodo": 3}],
        None, [],
    ),
    "POST /boletines/guardar": (
        [PROFESOR, ADMIN], "POST", "/boletines/guardar",
        {"estudiante_id": 3, "asignacion_id": 9, "periodo": 3, "definitiva": 4.0,
         "detalles": [{"nota": 4.0, "observacion": "ok"}]},
        None, [],
    ),
    "POST /observaciones": (
        [PROFESOR, ADMIN], "POST", "/observaciones",
        {"estudiante_id": 3, "asignacion_id": 9, "periodo": 3, "conductual": "Bien"}, None, [],
    ),
    "PUT /observador/{id}": ([PROFESOR], "PUT", "/observador/15", {"conductual": "Bien"}, None, []),
    "PUT /planeador-anual/{asignacion}/{periodo}": (
        [PROFESOR, ADMIN], "PUT", "/planeador-anual/9/3",
        [{"unidad_tematica": "U1", "fecha": "2026-10-30"}], None, [],
    ),
    "POST /plan-de-clases": (
        [PROFESOR, ADMIN], "POST", "/plan-de-clases", None,
        {"asignacion_id": "9", "fecha": "2026-10-05", "tema": "Fracciones"}, [],
    ),
    "DELETE /plan-de-clases/{id}/imagen": (
        [PROFESOR, ADMIN], "DELETE", "/plan-de-clases/20/imagen?slot=imagen1", None, None, IMAGEN,
    ),
    "PATCH /plan-de-clases/{id}/observaciones/{id}/vista": (
        [PROFESOR], "PATCH", "/plan-de-clases/20/observaciones/4/vista", None, None, [],
    ),
    "DELETE /admin/plan-de-clases/{id}/imagen": (
        [ADMIN], "DELETE", "/admin/plan-de-clases/20/imagen?slot=imagen1", None, None, IMAGEN,
    ),
    # --- Paso 3.7b: rutas de solo admin ---
    "POST /asignaciones": ([ADMIN], "POST", "/asignaciones", ASIGNACION, None, NUEVA_ASIGNACION),
    "PUT /asignaciones/{id}": (
        [ADMIN], "PUT", "/asignaciones/9", ASIGNACION, None,
        [("SELECT profesor_id, curso_id, materia_id, activo", (7, 2, 10, True, 9), [])]
        + NUEVA_ASIGNACION,
    ),
    "DELETE /asignaciones/{id}": ([ADMIN], "DELETE", "/asignaciones/9", None, None, []),
    "DELETE /asignaciones/{profesor}/{curso}": ([ADMIN], "DELETE", "/asignaciones/7/2", None, None, []),
    "PUT /cursos/{id}/orden-boletin": (
        [ADMIN], "PUT", "/cursos/2/orden-boletin",
        {"materias": [{"materia_id": 10}, {"materia_id": 12}]}, None,
        [("SELECT DISTINCT materia_id FROM asignaciones", Comodin(), [(10,), (12,)])],
    ),
    "PUT /cursos/{id}": (
        [ADMIN], "PUT", "/cursos/2", {"nombre": "PRIMERO A", "jornada": "Mañana"}, None,
        [("SELECT id FROM cursos WHERE UPPER", None, [])],
    ),
    "PATCH /cursos/{id}/estado": ([ADMIN], "PATCH", "/cursos/2/estado", {"estado": "inactivo"}, None, []),
    "POST /listas-seguimiento/{curso}/columnas": (
        [ADMIN], "POST", "/listas-seguimiento/2/columnas", {"nombre": "Tarea"}, None,
        [("SELECT 1 FROM listas_seguimiento_columnas", None, [])],
    ),
    "POST /listas-seguimiento/columnas-en-todos-los-cursos?anio_lectivo_id=5": (
        [ADMIN], "POST", "/listas-seguimiento/columnas-en-todos-los-cursos?anio_lectivo_id=5",
        {"nombre": "Tarea"}, None, _anio_pedido,
    ),
    "DELETE /listas-seguimiento/{curso}/columnas/{id}": (
        [ADMIN], "DELETE", "/listas-seguimiento/2/columnas/5", None, None, [],
    ),
    "POST /listas-seguimiento/{curso}/marcas": (
        [ADMIN], "POST", "/listas-seguimiento/2/marcas",
        [{"columna_id": 5, "estudiante_id": 3, "marcado": True}], None,
        [
            ("SELECT id, nombre FROM listas_seguimiento_columnas", Comodin(), [(5, "Tarea")]),
            ("SELECT e.id, e.nombre, e.apellido FROM matriculas m", Comodin(), [(3, "Ana", "Paz")]),
        ],
    ),
    "PATCH /admin/plan-de-clases/{id}/revision": (
        [ADMIN], "PATCH", "/admin/plan-de-clases/20/revision", {"estado": "visto", "version": 1},
        None, [],
    ),
    "POST /admin/plan-de-clases/{id}/observaciones": (
        [ADMIN], "POST", "/admin/plan-de-clases/20/observaciones",
        {"observacion": "Revisar", "version": 1}, None, [],
    ),
    "PUT /tipos-pagos/{id}": (
        [ADMIN], "PUT", "/tipos-pagos/4", {"nombre": "MENSUALIDAD", "valor": 0}, None,
        [("SELECT id FROM tipos_de_pagos WHERE LOWER(TRIM(nombre))", None, [])],
    ),
    "PUT /tipos-pagos/{id}/configuracion": (
        [ADMIN], "PUT", "/tipos-pagos/4/configuracion", {"dias_gracia": 5}, None,
        [
            ("FROM information_schema.columns", Comodin(), [(c,) for c in COLUMNAS_CONCEPTO]),
            ("FROM tipos_de_pagos", CONCEPTO, []),
        ],
    ),
    "PUT /tipos-pagos/{id}/cursos": (
        [ADMIN], "PUT", "/tipos-pagos/4/cursos", {"cursos": [{"curso_id": 2, "valor": 200000}]},
        None, [("SELECT ARRAY(", {"cursos_de_otro_anio": []}, [])],
    ),
    "DELETE /tipos-pagos/{id}/cursos/{curso}": (
        [ADMIN], "DELETE", "/tipos-pagos/4/cursos/2", None, None, [],
    ),
    "PUT /estudiantes/{id}/valores-pago-personalizados/{concepto}": (
        [ADMIN], "PUT", "/estudiantes/3/valores-pago-personalizados/4", {"valor": 150000}, None,
        CONTEXTO_VALOR_PERSONALIZADO,
    ),
    "DELETE /estudiantes/{id}/valores-pago-personalizados/{concepto}": (
        [ADMIN], "DELETE", "/estudiantes/3/valores-pago-personalizados/4", None, None, TABLAS,
    ),
}

CASOS = [(ruta, usuario["rol"]) for ruta, datos in RUTAS.items() for usuario in datos[0]]
USUARIOS = {"profesor": PROFESOR, "admin": ADMIN}


def _guardar(con_anio, ruta, rol, anio):
    _roles, metodo, url, cuerpo, formulario, respuestas = RUTAS[ruta]
    if callable(respuestas):
        respuestas = respuestas(anio)
    base = con_anio(anio, respuestas)
    status, respuesta = peticion(USUARIOS[rol], metodo, url, cuerpo, formulario)
    return base, status, respuesta


@pytest.mark.parametrize(("ruta", "rol"), CASOS, ids=lambda v: str(v))
def test_en_un_anio_cerrado_nadie_guarda(con_anio, ruta, rol):
    base, status, respuesta = _guardar(con_anio, ruta, rol, (2026, "cerrado"))

    assert status == 409
    assert respuesta == {"detail": CERRADO}
    assert base.escrituras == []
    assert base.commits == 0
    assert base.archivos_borrados == []


@pytest.mark.parametrize(("ruta", "rol"), CASOS, ids=lambda v: str(v))
@pytest.mark.parametrize("estado", ["preparacion", "reabierto"])
def test_el_profesor_solo_guarda_en_el_anio_activo_y_el_admin_tambien_en_los_otros(
    con_anio, ruta, rol, estado
):
    base, status, respuesta = _guardar(con_anio, ruta, rol, (2027, estado))

    if rol == "profesor":
        assert status == 403
        assert respuesta == {"detail": SOLO_ACTIVO}
        assert base.escrituras == []
        assert base.commits == 0
    else:
        assert status in (200, 201)
        assert base.escrituras
        assert base.commits >= 1


# Lo que mira la guardia en cada ruta (sus parametros): la clase 9 si no se
# dice otra cosa, el plan 20, la anotacion 15, el curso 2 o el concepto 4.
PARAMETROS_DE_LA_GUARDIA = {
    "PUT /observador/{id}": [(15,)],
    "DELETE /plan-de-clases/{id}/imagen": [(20,)],
    "PATCH /plan-de-clases/{id}/observaciones/{id}/vista": [(20,)],
    "DELETE /admin/plan-de-clases/{id}/imagen": [(20,)],
    "POST /asignaciones": [([2],)],
    # El curso de antes (2, el de la clase) y el nuevo (2), en una consulta.
    "PUT /asignaciones/{id}": [([2, 2],)],
    "DELETE /asignaciones/{id}": [(9,)],
    "DELETE /asignaciones/{profesor}/{curso}": [([2],)],
    "PUT /cursos/{id}/orden-boletin": [([2],)],
    "PUT /cursos/{id}": [([2],)],
    "PATCH /cursos/{id}/estado": [([2],)],
    "POST /listas-seguimiento/{curso}/columnas": [([2],)],
    # Sin consulta propia: usa la validacion del año que ya hacia.
    "POST /listas-seguimiento/columnas-en-todos-los-cursos?anio_lectivo_id=5": [],
    "DELETE /listas-seguimiento/{curso}/columnas/{id}": [([2],)],
    "POST /listas-seguimiento/{curso}/marcas": [([2],)],
    "PATCH /admin/plan-de-clases/{id}/revision": [(20,)],
    "POST /admin/plan-de-clases/{id}/observaciones": [(20,)],
    "PUT /tipos-pagos/{id}": [(4,)],
    "PUT /tipos-pagos/{id}/configuracion": [(4,)],
    "PUT /tipos-pagos/{id}/cursos": [(4,)],
    "DELETE /tipos-pagos/{id}/cursos/{curso}": [(4,)],
    "PUT /estudiantes/{id}/valores-pago-personalizados/{concepto}": [(4,)],
    "DELETE /estudiantes/{id}/valores-pago-personalizados/{concepto}": [(4,)],
}


@pytest.mark.parametrize(("ruta", "rol"), CASOS, ids=lambda v: str(v))
def test_la_guardia_mira_lo_que_se_guarda(con_anio, ruta, rol):
    base, _status, _ = _guardar(con_anio, ruta, rol, (2026, "activo"))

    assert base.ids_de_la_guardia == PARAMETROS_DE_LA_GUARDIA.get(ruta, [(9,)])


def test_columna_en_todos_los_cursos_sin_anio_no_consulta_la_guardia(con_anio):
    """Sin `?anio_lectivo_id=` son los cursos del activo, que siempre se puede
    editar: ni una consulta mas que antes."""
    base = con_anio((2026, "cerrado"))

    status, _ = peticion(
        ADMIN, "POST", "/listas-seguimiento/columnas-en-todos-los-cursos", {"nombre": "Tarea"}
    )

    assert status == 200
    assert base.ids_de_la_guardia == []
    assert not any(c.startswith(SQL_GUARDIA) for c in base.consultas)


@pytest.mark.parametrize(("ruta", "rol"), CASOS, ids=lambda v: str(v))
def test_en_el_anio_activo_se_guarda_como_siempre(con_anio, ruta, rol):
    base, status, _ = _guardar(con_anio, ruta, rol, (2026, "activo"))

    assert status in (200, 201)
    assert base.escrituras
    assert base.commits >= 1


def test_crear_un_plan_con_evidencia_en_un_anio_cerrado_borra_la_evidencia_subida(
    con_anio, monkeypatch
):
    """La evidencia se sube antes de abrir la transaccion. Si la guardia
    rechaza el guardado, el controlador la borra: no queda un archivo
    huerfano en el almacenamiento."""
    from app.controllers import plan_de_clases_controller

    monkeypatch.setattr(
        plan_de_clases_controller,
        "guardar_imagen_plan",
        lambda _dir, imagen: "planes/nueva.png" if imagen else None,
    )
    base = con_anio((2026, "cerrado"))

    # Se llama al controlador directamente: subir un archivo por HTTP exige
    # multipart, y lo que se prueba aqui es la limpieza, no el formulario.
    from app.schemas.plan_de_clases import PlanDeClasesCreate

    plan = PlanDeClasesCreate(asignacion_id=9, fecha="2026-10-05")
    with pytest.raises(HTTPException) as error:
        plan_de_clases_controller.crear_plan_de_clases_controller(
            plan, object(), None, usuario=PROFESOR
        )

    assert error.value.status_code == 409
    assert base.archivos_borrados == ["planes/nueva.png"]
    assert base.escrituras == []
