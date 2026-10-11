"""Año lectivo, fase 7, paso 7.1: traer el planeador anual del año pasado.

Ver `docs/funcionalidades/ANIO_LECTIVO.md`, fase 7 (decisiones 14 y 15). En su
planeador de 2027, si esta vacio, el profesor trae con un boton el de 2026 de
la misma materia en el curso del que se copio el suyo, lo haya escrito quien
lo haya escrito. Nunca reemplaza lo que ya haya escrito y no copia las fechas.

Si la materia cambio de profesor a mitad de 2026, el curso de 2026 tiene dos
planeadores (editar una clase con historial obliga a desactivarla y crear
otra). Decision del usuario del 2026-10-10: para cada periodo se trae lo del
ultimo profesor que escribio algo en ese periodo.

Las consultas no solo se leen como texto: corren de verdad en SQLite, que
viene con Python (el equipo no tiene PostgreSQL). Lo propio de PostgreSQL lo
confirma el ensayo en una rama de Neon.
"""
import asyncio
import json
import sqlite3

import pytest
from psycopg2 import IntegrityError, errorcodes

from app.controllers.planeador_anual_controller import (
    MENSAJE_CLASE_INEXISTENTE,
    MENSAJE_PLANEADOR_CON_CONTENIDO,
    MENSAJE_PLANEADOR_TRAIDO,
    MENSAJE_SIN_PLANEADOR_ANTERIOR,
)
from app.db import session
from app.repositories import planeador_anual_repository
from app.repositories.anios_lectivos_repository import CLASES_DE_ORIGEN_SQL
from app.services.anio_lectivo import (
    MENSAJE_ANIO_CERRADO,
    MENSAJE_SOLO_ANIO_ACTIVO,
    puede_guardar_en_anio,
)

PROFESORA_2027 = {"id": 8, "rol": "profesor"}
PROFESOR_QUE_LLEGO = {"id": 6, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}

MATEMATICAS, ESPANOL, ROBOTICA = 1, 2, 3

ESQUEMA = """
CREATE TABLE anios_lectivos (
    id INTEGER PRIMARY KEY, anio INTEGER NOT NULL, estado TEXT NOT NULL
);
CREATE TABLE cursos (
    id INTEGER PRIMARY KEY, nombre TEXT NOT NULL,
    anio_lectivo_id INTEGER NOT NULL, curso_origen_id INTEGER
);
CREATE TABLE asignaciones (
    id INTEGER PRIMARY KEY, profesor_id INTEGER, curso_id INTEGER,
    materia_id INTEGER, activo INTEGER, asignacion_academica_id INTEGER
);
CREATE TABLE planeador_anual (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asignacion_id INTEGER,
    periodo INTEGER NOT NULL,
    slot INTEGER NOT NULL,
    unidad_tematica TEXT,
    estandar_competencia TEXT,
    contenido TEXT,
    actividades_recursos TEXT,
    fecha TEXT,
    UNIQUE (asignacion_id, periodo, slot)
);
"""

CURSOS = [
    (10, "PRIMERO A", 1, None),
    (11, "PRIMERO B", 1, None),
    (20, "PRIMERO A", 2, 10),  # copiado de PRIMERO A 2026 (paso 5.4)
    (21, "TERCERO A", 2, None),  # creado desde cero en 2027
]

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

PLANEADOR_2026 = [
    # El que se fue escribio los periodos 1, 2 y 4.
    (100, 1, 1, "Números", "Cuenta", "Conteo", "Fichas", "2026-03-10"),
    (100, 1, 2, "Sumas", "Suma", "Sumas simples", "Ábaco", "2026-03-20"),
    (100, 2, 1, "Restas viejas", "", "", "", "2026-05-10"),
    (100, 2, 2, "Problemas viejos", "", "", "", "2026-05-20"),
    (100, 4, 1, "Fracciones", "", "", "", "2026-09-10"),
    # El que llego rehizo el periodo 2, escribio el 3 y dejo en el 4 una
    # fila sin texto, que no cuenta como escrita. En el 3 tambien quedo una
    # fila sin texto, que no se trae.
    (150, 2, 1, "Restas", "Resta", "Restas simples", "Guía", "2026-06-10"),
    (150, 3, 1, "Multiplicación", "", "Tablas", "", "2026-08-10"),
    (150, 3, 2, "", None, " ", "", "2026-08-20"),
    (150, 4, 1, "", "  ", None, "", "2026-10-10"),
    # Otra materia del mismo curso y la misma materia en otro curso.
    (110, 1, 1, "Lectura", "", "", "", "2026-03-10"),
    (120, 1, 1, "Números de otro curso", "", "", "", "2026-03-10"),
]

# Periodo, slot, los cuatro textos y la fecha, ya en la clase 200.
ESPERADO_EN_2027 = [
    (1, 1, "Números", "Cuenta", "Conteo", "Fichas", None),
    (1, 2, "Sumas", "Suma", "Sumas simples", "Ábaco", None),
    (2, 1, "Restas", "Resta", "Restas simples", "Guía", None),
    (3, 1, "Multiplicación", "", "Tablas", "", None),
    (4, 1, "Fracciones", "", "", "", None),
]


class UniqueViolation(IntegrityError):
    """El error de PostgreSQL por una fila repetida, como lo ve el controlador."""

    pgcode = errorcodes.UNIQUE_VIOLATION


class BaseSqlite:
    """Pool que entrega conexiones a una base SQLite en memoria con los datos de arriba."""

    def __init__(self, estados=("cerrado", "activo"), planeador_2027=()):
        # FastAPI atiende las rutas en otro hilo; las peticiones de una prueba
        # van de a una, asi que compartir la conexion es seguro.
        self.sqlite = sqlite3.connect(":memory:", check_same_thread=False)
        self.sqlite.executescript(ESQUEMA)
        self.sqlite.executemany(
            "INSERT INTO anios_lectivos VALUES (?, ?, ?)",
            [(1, 2026, estados[0]), (2, 2027, estados[1])],
        )
        self.sqlite.executemany("INSERT INTO cursos VALUES (?, ?, ?, ?)", CURSOS)
        self.sqlite.executemany(
            "INSERT INTO asignaciones VALUES (?, ?, ?, ?, ?, ?)", ASIGNACIONES
        )
        self.sqlite.executemany(
            "INSERT INTO planeador_anual (asignacion_id, periodo, slot, unidad_tematica,"
            " estandar_competencia, contenido, actividades_recursos, fecha)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            PLANEADOR_2026 + list(planeador_2027),
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

    def planeador_de(self, asignacion_id):
        return self.sqlite.execute(
            "SELECT periodo, slot, unidad_tematica, estandar_competencia, contenido,"
            " actividades_recursos, fecha FROM planeador_anual"
            " WHERE asignacion_id = ? ORDER BY periodo, slot",
            (asignacion_id,),
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
        try:
            self._cursor.execute(str(sql).replace("%s", "?"), tuple(params or ()))
        except sqlite3.IntegrityError as exc:
            raise UniqueViolation(str(exc)) from exc

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


def peticion(usuario, metodo, ruta):
    """Una peticion real contra la app con `usuario` en sesion."""
    from app.dependencies import get_current_user
    from app.main import app

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
        "headers": [(b"host", b"testserver"), (b"content-length", b"0")],
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


def consultar(usuario, clase):
    return peticion(usuario, "GET", f"/planeador-anual/{clase}/anio-anterior")


def traer(usuario, clase):
    return peticion(usuario, "POST", f"/planeador-anual/{clase}/anio-anterior")


# ---------------------------------------------------------------------------
# La regla del origen y los mensajes.
# ---------------------------------------------------------------------------


def test_el_origen_es_la_misma_materia_en_el_curso_del_que_se_copio():
    texto = " ".join(CLASES_DE_ORIGEN_SQL.split())

    assert "origen.curso_id = curso_destino.curso_origen_id" in texto
    assert "origen.materia_id = destino.materia_id" in texto
    assert texto.count("%s") == 1
    # Decision 15: sigue al curso y la materia, no a la persona; y una clase
    # desactivada (el profesor que se fue) tambien cuenta.
    assert "profesor" not in texto
    assert "activo" not in texto


def test_los_mensajes_estan_listos_para_mostrar():
    assert MENSAJE_PLANEADOR_TRAIDO == (
        "Se trajo el planeador del año pasado. Las fechas quedaron vacías: "
        "pon las de este año al guardar cada periodo."
    )
    assert MENSAJE_PLANEADOR_CON_CONTENIDO == (
        "Este planeador ya tiene contenido. No se trajo nada, para no "
        "reemplazar lo que ya está escrito."
    )
    assert MENSAJE_SIN_PLANEADOR_ANTERIOR == (
        "No hay un planeador del año pasado para traer a esta clase."
    )
    assert MENSAJE_CLASE_INEXISTENTE == "La clase no existe."


@pytest.mark.parametrize(
    ("estado", "usuario", "puede"),
    [
        ("activo", PROFESORA_2027, True),
        ("activo", ADMIN, True),
        ("preparacion", PROFESORA_2027, False),
        ("preparacion", ADMIN, True),
        ("reabierto", PROFESORA_2027, False),
        ("reabierto", ADMIN, True),
        ("cerrado", PROFESORA_2027, False),
        ("cerrado", ADMIN, False),
    ],
)
def test_puede_guardar_en_anio_es_la_regla_de_la_guardia_sin_lanzar(estado, usuario, puede):
    assert puede_guardar_en_anio((2027, estado), usuario) is puede


# ---------------------------------------------------------------------------
# Las consultas del repositorio, corridas en SQLite.
# ---------------------------------------------------------------------------


def test_cada_periodo_sale_del_ultimo_profesor_que_lo_escribio():
    base = BaseSqlite()
    cursor = CursorSqlite(base)

    copiadas = planeador_anual_repository.copiar_planeador_anio_anterior(cursor, 200, 200)

    assert copiadas == 5
    # Periodo 1 y 4 del que se fue; 2 y 3 del que llego. El periodo 2 sale
    # entero del que llego: el slot 2 viejo no se mezcla con el slot 1 nuevo.
    # La fila sin texto del periodo 4 no le quita ese periodo al que se fue.
    # Otra materia y otro curso no se traen. Ninguna fecha se copia.
    assert base.planeador_de(200) == ESPERADO_EN_2027
    assert len(base.consultas) == 1
    assert base.consultas[0].startswith("INSERT INTO planeador_anual")


def test_el_planeador_de_2026_no_cambia_al_traerlo():
    base = BaseSqlite()
    antes = {clase: base.planeador_de(clase) for clase in (100, 150, 110, 120)}

    planeador_anual_repository.copiar_planeador_anio_anterior(CursorSqlite(base), 200, 200)

    assert {clase: base.planeador_de(clase) for clase in antes} == antes


@pytest.mark.parametrize("clase", [210, 220], ids=["curso_sin_origen", "materia_nueva"])
def test_sin_origen_no_hay_nada_que_traer(clase):
    base = BaseSqlite()
    cursor = CursorSqlite(base)

    assert planeador_anual_repository.copiar_planeador_anio_anterior(cursor, clase, clase) == 0
    assert planeador_anual_repository.leer_planeador_anio_anterior(
        cursor, clase, clase
    ) == (2027, "activo", 0, 0)


def test_el_estado_es_una_sola_consulta_con_el_anio_las_filas_y_el_origen():
    base = BaseSqlite(planeador_2027=[(200, 3, 1, "Ya escrito", "", "", "", None)])
    cursor = CursorSqlite(base)

    assert planeador_anual_repository.leer_planeador_anio_anterior(
        cursor, 200, 200
    ) == (2027, "activo", 1, 1)
    assert planeador_anual_repository.leer_planeador_anio_anterior(
        cursor, 210, 210
    ) == (2027, "activo", 0, 0)
    assert planeador_anual_repository.leer_planeador_anio_anterior(cursor, 999, 999) is None
    assert len(base.consultas) == 3


# ---------------------------------------------------------------------------
# Las dos rutas, por la aplicacion real, con la base SQLite.
# ---------------------------------------------------------------------------


def test_la_profesora_de_2027_ve_que_puede_traer_el_planeador(con_base):
    base = con_base()

    assert consultar(PROFESORA_2027, 200) == (
        200,
        {"hay_origen": True, "planeador_vacio": True, "puede_traer": True},
    )
    assert base.planeador_de(200) == []
    assert base.commits == 0


def test_traer_copia_el_planeador_y_responde_cuantas_filas(con_base):
    base = con_base()

    assert traer(PROFESORA_2027, 200) == (
        200,
        {"message": MENSAJE_PLANEADOR_TRAIDO, "filas_copiadas": 5},
    )
    assert base.planeador_de(200) == ESPERADO_EN_2027
    assert base.commits == 1
    # Despues, el boton ya no se ofrece.
    assert consultar(PROFESORA_2027, 200) == (
        200,
        {"hay_origen": True, "planeador_vacio": False, "puede_traer": False},
    )


def test_lo_traido_se_ve_en_el_planeador_de_cada_periodo_sin_fecha(con_base):
    con_base()
    traer(PROFESORA_2027, 200)

    status, cuerpo = peticion(PROFESORA_2027, "GET", "/planeador-anual/200/2")

    assert status == 200
    assert [
        (fila["periodo"], fila["slot"], fila["unidad_tematica"], fila["fecha"])
        for fila in cuerpo["planeadores"]
    ] == [(2, 1, "Restas", None)]


def test_desde_otra_franja_de_la_clase_se_guarda_en_la_clase_academica(con_base):
    base = con_base()

    assert consultar(PROFESORA_2027, 201)[1]["puede_traer"] is True
    assert traer(PROFESORA_2027, 201)[0] == 200

    assert base.planeador_de(200) == ESPERADO_EN_2027
    assert base.planeador_de(201) == []


def test_desde_otra_franja_tambien_se_ve_lo_ya_escrito_en_la_clase(con_base):
    # El planeador se guarda en la clase academica (200): pedido desde la
    # franja 201, lo escrito en la 200 tambien cuenta.
    ya_escrito = [(200, 3, 7, "Ya escrito", "", "", "", "2027-08-01")]
    base = con_base(planeador_2027=ya_escrito)

    assert consultar(PROFESORA_2027, 201)[1]["planeador_vacio"] is False
    assert traer(PROFESORA_2027, 201) == (409, {"detail": MENSAJE_PLANEADOR_CON_CONTENIDO})
    assert base.planeador_de(200) == [(3, 7, "Ya escrito", "", "", "", "2027-08-01")]


def test_con_algo_ya_escrito_no_se_trae_nada(con_base):
    # Un slot que la copia no usa: sin la revision previa, la copia no
    # chocaria con nada y mezclaria lo traido con lo escrito.
    ya_escrito = [(200, 3, 7, "Ya escrito", "", "", "", "2027-08-01")]
    base = con_base(planeador_2027=ya_escrito)

    assert consultar(PROFESORA_2027, 200) == (
        200,
        {"hay_origen": True, "planeador_vacio": False, "puede_traer": False},
    )
    assert traer(PROFESORA_2027, 200) == (409, {"detail": MENSAJE_PLANEADOR_CON_CONTENIDO})
    assert base.planeador_de(200) == [(3, 7, "Ya escrito", "", "", "", "2027-08-01")]
    assert base.commits == 0


@pytest.mark.parametrize("clase", [210, 220], ids=["curso_sin_origen", "materia_nueva"])
def test_sin_origen_no_se_ofrece_y_traer_responde_404(con_base, clase):
    base = con_base()

    assert consultar(PROFESORA_2027, clase) == (
        200,
        {"hay_origen": False, "planeador_vacio": True, "puede_traer": False},
    )
    assert traer(PROFESORA_2027, clase) == (404, {"detail": MENSAJE_SIN_PLANEADOR_ANTERIOR})
    assert base.planeador_de(clase) == []
    assert base.commits == 0


def test_un_profesor_que_no_dicta_la_clase_recibe_403(con_base):
    # El 6 escribio parte del planeador de 2026, pero la clase de 2027 no es suya.
    base = con_base()

    assert consultar(PROFESOR_QUE_LLEGO, 200) == (403, {"detail": "No autorizado"})
    assert traer(PROFESOR_QUE_LLEGO, 200) == (403, {"detail": "No autorizado"})
    assert base.planeador_de(200) == []
    assert base.commits == 0


def test_el_profesor_solo_trae_en_el_anio_activo_y_el_admin_tambien_en_preparacion(con_base):
    base = con_base(estados=("activo", "preparacion"))

    assert consultar(PROFESORA_2027, 200)[1]["puede_traer"] is False
    assert traer(PROFESORA_2027, 200) == (403, {"detail": MENSAJE_SOLO_ANIO_ACTIVO})
    assert base.planeador_de(200) == []

    assert consultar(ADMIN, 200)[1]["puede_traer"] is True
    assert traer(ADMIN, 200)[0] == 200
    assert base.planeador_de(200) == ESPERADO_EN_2027


@pytest.mark.parametrize("usuario", [PROFESORA_2027, ADMIN], ids=["profesor", "admin"])
def test_en_un_anio_cerrado_nadie_trae(con_base, usuario):
    base = con_base(estados=("cerrado", "cerrado"))

    assert consultar(usuario, 200)[1]["puede_traer"] is False
    assert traer(usuario, 200) == (
        409,
        {"detail": MENSAJE_ANIO_CERRADO.format(anio=2027)},
    )
    assert base.planeador_de(200) == []
    assert base.commits == 0


def test_una_clase_que_no_existe_responde_404(con_base):
    base = con_base()

    assert consultar(ADMIN, 999) == (404, {"detail": MENSAJE_CLASE_INEXISTENTE})
    assert traer(ADMIN, 999) == (404, {"detail": MENSAJE_CLASE_INEXISTENTE})
    assert base.commits == 0


def test_dos_clics_a_la_vez_el_segundo_recibe_409_y_no_queda_nada_a_medias(
    con_base, monkeypatch
):
    # El segundo clic leyo el planeador vacio justo antes de que el primero
    # guardara: su INSERT choca con la regla unica (clase, periodo, slot).
    base = con_base(planeador_2027=[(200, 1, 1, "Del primer clic", "", "", "", None)])
    leer = planeador_anual_repository.leer_planeador_anio_anterior

    def leer_como_antes_del_primer_clic(cursor, asignacion_id, destino_id):
        anio, estado, _, hay_origen = leer(cursor, asignacion_id, destino_id)
        return anio, estado, 0, hay_origen

    monkeypatch.setattr(
        planeador_anual_repository,
        "leer_planeador_anio_anterior",
        leer_como_antes_del_primer_clic,
    )

    assert traer(PROFESORA_2027, 200) == (409, {"detail": MENSAJE_PLANEADOR_CON_CONTENIDO})
    assert base.planeador_de(200) == [(1, 1, "Del primer clic", "", "", "", None)]
    assert base.commits == 0


def test_la_ruta_de_un_periodo_sigue_igual(con_base):
    # Las rutas nuevas van antes en el router: "anio-anterior" no se lee como
    # periodo, y un periodo sigue llegando a su ruta de siempre.
    con_base(planeador_2027=[(200, 2, 1, "U1", "", "", "", "2027-05-01")])

    status, cuerpo = peticion(PROFESORA_2027, "GET", "/planeador-anual/200/2")

    assert status == 200
    assert list(cuerpo) == ["planeadores"]
    assert [fila["unidad_tematica"] for fila in cuerpo["planeadores"]] == ["U1"]


@pytest.mark.parametrize(
    ("usuario", "consultas_get", "consultas_post"),
    [(PROFESORA_2027, 3, 4), (ADMIN, 2, 3)],
    ids=["profesor", "admin"],
)
def test_cada_ruta_usa_una_conexion_y_pocas_consultas(
    con_base, usuario, consultas_get, consultas_post
):
    # Profesor: su permiso, la clase academica y el estado (y el INSERT al
    # traer). El admin no necesita el permiso. La guardia del año usa el
    # estado ya leido: no cuesta una consulta mas.
    base = con_base()

    consultar(usuario, 200)
    assert (base.conexiones, len(base.consultas)) == (1, consultas_get)

    base.conexiones, base.consultas = 0, []
    traer(usuario, 200)
    assert (base.conexiones, len(base.consultas)) == (1, consultas_post)
