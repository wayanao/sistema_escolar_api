"""Año lectivo, fase 7, paso 7.2: usar un plan de clases del año pasado.

Ver `docs/funcionalidades/ANIO_LECTIVO.md`, fase 7 (decisiones 15 y 16). Al
crear un plan en 2027, el profesor elige uno de 2026 de la misma materia en el
curso del que se copio el suyo, lo haya escrito quien lo haya escrito; el
formulario se llena con su texto y el profesor lo guarda por la ruta normal,
como un plan nuevo. La fecha y las evidencias no se copian. El profesor solo
manda su clase de 2027 y el id del plan; el backend comprueba que el plan sea
del origen de esa clase. Estas rutas solo leen: no crean nada.

Como en el paso 7.1, las consultas corren de verdad en SQLite (viene con
Python; el equipo no tiene PostgreSQL). Lo propio de PostgreSQL lo confirma
el ensayo en una rama de Neon.
"""
import asyncio
import json
import sqlite3

import pytest

from app.controllers.plan_de_clases_controller import MENSAJE_PLAN_NO_ES_DEL_ANIO_ANTERIOR
from app.db import session
from app.repositories.anios_lectivos_repository import CLASES_DE_ORIGEN_SQL
from app.services.anio_lectivo import MENSAJE_ANIO_CERRADO, MENSAJE_SOLO_ANIO_ACTIVO

PROFESORA_2027 = {"id": 8, "rol": "profesor"}
PROFESOR_QUE_LLEGO = {"id": 6, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}
SIN_PERMISO = "No tienes permisos para esta asignación"

MATEMATICAS, ESPANOL, ROBOTICA = 1, 2, 3

ESQUEMA = """
CREATE TABLE anios_lectivos (
    id INTEGER PRIMARY KEY, anio INTEGER NOT NULL, estado TEXT NOT NULL
);
CREATE TABLE cursos (
    id INTEGER PRIMARY KEY, nombre TEXT NOT NULL,
    anio_lectivo_id INTEGER NOT NULL, curso_origen_id INTEGER
);
CREATE TABLE materias (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL);
CREATE TABLE profesor (id INTEGER PRIMARY KEY, nombre TEXT, apellido TEXT);
CREATE TABLE asignaciones (
    id INTEGER PRIMARY KEY, profesor_id INTEGER, curso_id INTEGER,
    materia_id INTEGER, activo INTEGER, asignacion_academica_id INTEGER
);
CREATE TABLE plan_de_clases (
    id INTEGER PRIMARY KEY,
    asignacion_id INTEGER NOT NULL,
    unidad TEXT NOT NULL,
    proposito TEXT,
    estandar TEXT,
    dba TEXT,
    competencias TEXT,
    tema TEXT,
    fecha TEXT NOT NULL,
    imagen1 TEXT,
    imagen2 TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    periodo INTEGER DEFAULT 1,
    clase TEXT DEFAULT '',
    actividad_casa TEXT DEFAULT '',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    estado_revision TEXT NOT NULL DEFAULT 'pendiente',
    version_revision INTEGER NOT NULL DEFAULT 1,
    enviado_at TEXT DEFAULT CURRENT_TIMESTAMP,
    admin_visto_at TEXT,
    revisado_at TEXT,
    UNIQUE (asignacion_id, fecha)
);
CREATE TABLE plan_de_clases_observaciones (
    id INTEGER PRIMARY KEY, plan_id INTEGER, vista_por_profesor_at TEXT,
    creada_at TEXT
);
"""

CURSOS = [
    (10, "PRIMERO A", 1, None),
    (11, "PRIMERO B", 1, None),
    (20, "PRIMERO A", 2, 10),  # copiado de PRIMERO A 2026 (paso 5.4)
    (21, "TERCERO A", 2, None),  # creado desde cero en 2027
]
MATERIAS = [(MATEMATICAS, "MATEMÁTICAS"), (ESPANOL, "ESPAÑOL"), (ROBOTICA, "ROBÓTICA")]
PROFESORES = [(5, "Ana", "Ríos"), (6, "Luis", "Paz"), (8, "Marta", "Gil"), (9, "Eva", "Sol")]

ASIGNACIONES = [
    # 2026, PRIMERO A, Matematicas: el profesor 5 se fue a mitad de año (su
    # clase quedo desactivada) y el 6 llego con una clase nueva.
    (100, 5, 10, MATEMATICAS, 0, None),
    (150, 6, 10, MATEMATICAS, 1, None),
    (110, 5, 10, ESPANOL, 1, None),
    (120, 9, 11, MATEMATICAS, 1, None),
    # 2027: la profesora 8 no dictaba en 2026 (decision 15).
    (200, 8, 20, MATEMATICAS, 1, None),
    (201, 8, 20, MATEMATICAS, 1, 200),  # otra franja de la misma clase
    (210, 8, 21, MATEMATICAS, 1, None),
    (220, 8, 20, ROBOTICA, 1, None),
]

COLUMNAS_PLAN = (
    "id, asignacion_id, periodo, unidad, proposito, clase, estandar, dba,"
    " competencias, actividad_casa, tema, fecha, imagen1, imagen2, estado_revision"
)
PLANES = [
    # Del profesor que se fue, con sus evidencias y ya revisado.
    (1, 100, 1, "Números", "Contar", "Conteo con fichas", "E1", "D1", "C1",
     "Contar en casa", "Conteo", "2026-02-10", "planes/a.png", "planes/b.pdf", "revisado"),
    # Del que llego; uno con textos vacios.
    (2, 150, 2, "Restas", None, None, None, None, None, None, "Restar",
     "2026-05-12", None, None, "pendiente"),
    (3, 150, 1, "Sumas", "Sumar", "", "E2", "D2", "C2", "", "Sumar",
     "2026-03-03", None, None, "con_observaciones"),
    # Otra materia del mismo curso y la misma materia en otro curso.
    (4, 110, 1, "Lectura", "", "", "", "", "", "", "Leer", "2026-02-10", None, None, "pendiente"),
    (5, 120, 1, "Números B", "", "", "", "", "", "", "Contar", "2026-02-10", None, None, "pendiente"),
    # El plan de 2027 de la propia clase: no es del año pasado.
    (9, 200, 1, "Repaso", "", "", "", "", "", "", "Repasar", "2027-02-15", None, None, "pendiente"),
]

LISTA_ESPERADA = [
    {"id": 1, "fecha": "2026-02-10", "periodo": 1, "unidad": "Números", "tema": "Conteo"},
    {"id": 3, "fecha": "2026-03-03", "periodo": 1, "unidad": "Sumas", "tema": "Sumar"},
    {"id": 2, "fecha": "2026-05-12", "periodo": 2, "unidad": "Restas", "tema": "Restar"},
]


class BaseSqlite:
    """Pool que entrega conexiones a una base SQLite en memoria con los datos de arriba."""

    def __init__(self, estados=("cerrado", "activo")):
        # FastAPI atiende las rutas en otro hilo; las peticiones de una prueba
        # van de a una, asi que compartir la conexion es seguro.
        self.sqlite = sqlite3.connect(":memory:", check_same_thread=False)
        self.sqlite.executescript(ESQUEMA)
        self.sqlite.executemany(
            "INSERT INTO anios_lectivos VALUES (?, ?, ?)",
            [(1, 2026, estados[0]), (2, 2027, estados[1])],
        )
        self.sqlite.executemany("INSERT INTO cursos VALUES (?, ?, ?, ?)", CURSOS)
        self.sqlite.executemany("INSERT INTO materias VALUES (?, ?)", MATERIAS)
        self.sqlite.executemany("INSERT INTO profesor VALUES (?, ?, ?)", PROFESORES)
        self.sqlite.executemany(
            "INSERT INTO asignaciones VALUES (?, ?, ?, ?, ?, ?)", ASIGNACIONES
        )
        self.sqlite.executemany(
            f"INSERT INTO plan_de_clases ({COLUMNAS_PLAN}) VALUES ({', '.join('?' * 15)})",
            PLANES,
        )
        self.sqlite.commit()
        self.conexiones = 0
        self.consultas = []
        self.commits = 0

    def getconn(self):
        self.conexiones += 1
        return ConexionSqlite(self)

    def putconn(self, conexion, close=False):
        pass

    def planes(self):
        return self.sqlite.execute(
            f"SELECT {COLUMNAS_PLAN} FROM plan_de_clases ORDER BY id"
        ).fetchall()


class ConexionSqlite:
    def __init__(self, base):
        self.base = base
        self.autocommit = False

    def cursor(self, *args, **kwargs):
        return CursorSqlite(self.base)

    def commit(self):
        self.base.commits += 1
        self.base.sqlite.commit()

    def rollback(self):
        self.base.sqlite.rollback()

    def close(self):
        pass


class CursorSqlite:
    """Cursor de SQLite con los `%s` de psycopg2."""

    def __init__(self, base):
        self.base = base
        self._cursor = base.sqlite.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=()):
        self.base.consultas.append(" ".join(str(sql).split()))
        self._cursor.execute(str(sql).replace("%s", "?"), tuple(params or ()))

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        pass


@pytest.fixture
def con_base(monkeypatch):
    def usar(**kwargs):
        base = BaseSqlite(**kwargs)
        monkeypatch.setattr(session, "apply_session_setup", lambda cursor: None)
        monkeypatch.setattr(session, "get_pool", lambda: base)
        return base

    return usar


def peticion(usuario, ruta):
    """Un GET real contra la app con `usuario` en sesion."""
    from app.dependencies import get_current_user
    from app.main import app

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

    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        asyncio.run(app(scope, receive, send))
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    return salida["status"], json.loads(salida["body"].decode() or "null")


def lista(usuario, clase):
    return peticion(usuario, f"/plan-de-clases/{clase}/anio-anterior")


def plan(usuario, clase, plan_id):
    return peticion(usuario, f"/plan-de-clases/{clase}/anio-anterior/{plan_id}")


def test_el_mensaje_esta_listo_para_mostrar():
    assert MENSAJE_PLAN_NO_ES_DEL_ANIO_ANTERIOR == (
        "Ese plan no es del año pasado de esta clase."
    )


# ---------------------------------------------------------------------------
# La lista.
# ---------------------------------------------------------------------------


def test_la_lista_trae_los_planes_de_la_materia_en_el_curso_de_origen(con_base):
    # De los dos profesores de 2026 (tambien del que se fue), por fecha. Ni
    # otra materia, ni otro curso, ni el plan de 2027 de la propia clase.
    base = con_base()

    assert lista(PROFESORA_2027, 200) == (200, LISTA_ESPERADA)
    assert " ".join(CLASES_DE_ORIGEN_SQL.split()) in base.consultas[-1]


def test_desde_otra_franja_de_la_clase_la_lista_es_la_misma(con_base):
    con_base()

    assert lista(PROFESORA_2027, 201) == (200, LISTA_ESPERADA)


@pytest.mark.parametrize("clase", [210, 220], ids=["curso_sin_origen", "materia_nueva"])
def test_sin_origen_la_lista_esta_vacia(con_base, clase):
    con_base()

    assert lista(PROFESORA_2027, clase) == (200, [])


# ---------------------------------------------------------------------------
# El texto de un plan.
# ---------------------------------------------------------------------------


def test_el_texto_de_un_plan_viene_sin_fecha_sin_evidencias_y_sin_periodo(con_base):
    # Decision 16: solo el texto para llenar el formulario. El periodo queda el
    # que el profesor tiene elegido (regla del 2026-10-10).
    con_base()

    assert plan(PROFESORA_2027, 200, 1) == (
        200,
        {
            "id": 1,
            "unidad": "Números",
            "proposito": "Contar",
            "clase": "Conteo con fichas",
            "estandar": "E1",
            "dba": "D1",
            "competencias": "C1",
            "actividad_casa": "Contar en casa",
            "tema": "Conteo",
        },
    )


def test_un_texto_vacio_llega_como_cadena_vacia(con_base):
    con_base()

    status, cuerpo = plan(PROFESORA_2027, 201, 2)

    assert status == 200
    assert cuerpo == {
        "id": 2,
        "unidad": "Restas",
        "proposito": "",
        "clase": "",
        "estandar": "",
        "dba": "",
        "competencias": "",
        "actividad_casa": "",
        "tema": "Restar",
    }


@pytest.mark.parametrize(
    "plan_id",
    [4, 5, 9, 999],
    ids=["otra_materia", "otro_curso", "plan_de_2027", "no_existe"],
)
def test_un_plan_que_no_es_del_origen_responde_403(con_base, plan_id):
    con_base()

    assert plan(PROFESORA_2027, 200, plan_id) == (
        403,
        {"detail": MENSAJE_PLAN_NO_ES_DEL_ANIO_ANTERIOR},
    )


def test_desde_una_clase_sin_origen_ningun_plan_sirve(con_base):
    con_base()

    assert plan(PROFESORA_2027, 210, 1) == (
        403,
        {"detail": MENSAJE_PLAN_NO_ES_DEL_ANIO_ANTERIOR},
    )


# ---------------------------------------------------------------------------
# Permisos y año.
# ---------------------------------------------------------------------------


def test_un_profesor_que_no_dicta_la_clase_recibe_403(con_base):
    # El 6 escribio planes de 2026, pero la clase de 2027 no es suya.
    con_base()

    assert lista(PROFESOR_QUE_LLEGO, 200) == (403, {"detail": SIN_PERMISO})
    assert plan(PROFESOR_QUE_LLEGO, 200, 1) == (403, {"detail": SIN_PERMISO})


def test_el_profesor_solo_desde_el_anio_activo_y_el_admin_tambien_en_preparacion(con_base):
    con_base(estados=("activo", "preparacion"))

    assert lista(PROFESORA_2027, 200) == (403, {"detail": MENSAJE_SOLO_ANIO_ACTIVO})
    assert plan(PROFESORA_2027, 200, 1) == (403, {"detail": MENSAJE_SOLO_ANIO_ACTIVO})

    assert lista(ADMIN, 200) == (200, LISTA_ESPERADA)
    assert plan(ADMIN, 200, 1)[0] == 200


@pytest.mark.parametrize("usuario", [PROFESORA_2027, ADMIN], ids=["profesor", "admin"])
def test_desde_un_anio_cerrado_nadie(con_base, usuario):
    con_base(estados=("cerrado", "cerrado"))
    cerrado = (409, {"detail": MENSAJE_ANIO_CERRADO.format(anio=2027)})

    assert lista(usuario, 200) == cerrado
    assert plan(usuario, 200, 1) == cerrado


def test_solo_leen_no_escriben_nada(con_base):
    base = con_base()
    antes = base.planes()

    lista(PROFESORA_2027, 200)
    plan(PROFESORA_2027, 200, 1)
    plan(PROFESORA_2027, 200, 4)

    assert base.planes() == antes
    assert base.commits == 0
    assert not any(
        consulta.split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}
        for consulta in base.consultas
    )


def test_la_ruta_de_los_planes_de_la_clase_sigue_igual(con_base):
    # GET /plan-de-clases/{asignacion_id}: los planes de la propia clase, como siempre.
    con_base()

    status, cuerpo = peticion(PROFESORA_2027, "/plan-de-clases/200")

    assert status == 200
    assert [(p["id"], p["unidad"], p["fecha"]) for p in cuerpo] == [(9, "Repaso", "2027-02-15")]


@pytest.mark.parametrize(
    ("usuario", "conexiones", "consultas"),
    [(PROFESORA_2027, 2, 3), (ADMIN, 1, 2)],
    ids=["profesor", "admin"],
)
@pytest.mark.parametrize("ruta", ["lista", "plan"])
def test_cada_ruta_cuesta_lo_mismo_que_los_planes_de_la_clase(
    con_base, usuario, conexiones, consultas, ruta
):
    # Como GET /plan-de-clases/{asignacion_id}: el permiso del profesor en su
    # propia conexion (en la ruta, como las demas de planes) y, en otra, la
    # guardia del año y la lectura.
    base = con_base()

    if ruta == "lista":
        lista(usuario, 200)
    else:
        plan(usuario, 200, 1)

    assert (base.conexiones, len(base.consultas)) == (conexiones, consultas)
