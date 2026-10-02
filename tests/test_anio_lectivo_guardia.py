"""Año lectivo, paso 3.7: la guardia de escritura.

Ver `docs/funcionalidades/ANIO_LECTIVO.md`, "La guardia de escritura". Nadie
escribe en un año cerrado (409); el profesor solo escribe en el activo (403 en
uno en preparacion o reabierto); el admin escribe en el activo, en el de
preparacion y en uno reabierto. Con el año activo, como hoy, todo sigue igual.

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
    leer_anio_de_plan,
)
from app.services.anio_lectivo import (
    MENSAJE_ANIO_CERRADO,
    MENSAJE_SOLO_ANIO_ACTIVO,
    AnioLectivoNoEditableError,
    exigir_anio_editable,
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


@pytest.mark.parametrize("leer", [leer_anio_de_asignacion, leer_anio_de_plan, leer_anio_de_anotacion])
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
        self.respuestas = [(SQL_GUARDIA, anio, [])] + list(respuestas)

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
}

CASOS = [(ruta, usuario["rol"]) for ruta, datos in RUTAS.items() for usuario in datos[0]]
USUARIOS = {"profesor": PROFESOR, "admin": ADMIN}


def _guardar(con_anio, ruta, rol, anio):
    _roles, metodo, url, cuerpo, formulario, respuestas = RUTAS[ruta]
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


# Lo que mira la guardia en cada ruta: la clase, el plan o la anotacion.
ID_QUE_MIRA = {
    "PUT /observador/{id}": 15,
    "DELETE /plan-de-clases/{id}/imagen": 20,
    "PATCH /plan-de-clases/{id}/observaciones/{id}/vista": 20,
    "DELETE /admin/plan-de-clases/{id}/imagen": 20,
}


@pytest.mark.parametrize(("ruta", "rol"), CASOS, ids=lambda v: str(v))
def test_la_guardia_mira_lo_que_se_guarda(con_anio, ruta, rol):
    base, _status, _ = _guardar(con_anio, ruta, rol, (2026, "activo"))

    # Clase 9 en las rutas que guardan sobre una clase.
    assert base.ids_de_la_guardia == [(ID_QUE_MIRA.get(ruta, 9),)]


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
