"""«Mi curso» del director de grupo: paso 1 (lectura) y paso 3 (observación
general).

Ver docs/funcionalidades/MI_CURSO_DIRECTOR.md. Cubre el permiso nuevo
(`require_director_de_curso`), el armado del ranking con las reglas del
boletin, que el curso entero salga en un numero fijo de consultas, y las rutas
por la interfaz ASGI real, como `test_admisiones_routes.py`.
"""
import asyncio
import json
from contextlib import contextmanager
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.controllers import director_grupo_controller as controlador
from app.core import permissions
from app.core.nivel_academico import NOMBRE_MATERIA_ASISTENCIA_JORNADA
from app.routes import director_grupo as rutas

ADMIN = {"id": 1, "rol": "admin"}
DIRECTOR = {"id": 7, "rol": "profesor"}


# ---------------------------------------------------------------------------
# Dobles
# ---------------------------------------------------------------------------


class CursorFalso:
    """Registra cada `execute` y sirve las respuestas en orden."""

    def __init__(self, respuestas=()):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.cerrado = False

    def execute(self, sql, params=None):
        self.llamadas.append((sql, params))

    def _siguiente(self):
        return self.respuestas.pop(0) if self.respuestas else None

    def fetchone(self):
        return self._siguiente()

    def fetchall(self):
        return self._siguiente() or []

    def close(self):
        self.cerrado = True


class ConexionFalsa:
    def __init__(self, cursor):
        self.cursor_instancia = cursor
        self.cerrada = False

    def cursor(self, *args, **kwargs):
        return self.cursor_instancia

    def close(self):
        self.cerrada = True


def doblar_get_cursor(monkeypatch, cursor):
    pedidos = []

    @contextmanager
    def falso(commit=False, cursor_factory=None):
        pedidos.append({"commit": commit, "cursor_factory": cursor_factory})
        yield cursor

    monkeypatch.setattr(controlador, "get_cursor", falso)
    return pedidos


# ---------------------------------------------------------------------------
# Permiso: require_director_de_curso
# ---------------------------------------------------------------------------


def test_el_admin_pasa_sin_consultar_la_base(monkeypatch):
    def no_debe(*_):
        raise AssertionError("El admin no consulta la base para este permiso")

    monkeypatch.setattr(permissions, "get_connection", no_debe)
    permissions.require_director_de_curso(5, ADMIN)


def test_el_director_del_curso_del_anio_activo_pasa(monkeypatch):
    cursor = CursorFalso([(1,)])
    conexion = ConexionFalsa(cursor)
    monkeypatch.setattr(permissions, "get_connection", lambda: conexion)

    permissions.require_director_de_curso(5, DIRECTOR)

    sql, params = cursor.llamadas[0]
    assert params == (5, 7)
    assert "c.director_grupo_id = %s" in sql
    assert "anios_lectivos WHERE estado = 'activo'" in sql
    assert cursor.cerrado is True
    assert conexion.cerrada is True


def test_un_profesor_que_no_dirige_el_curso_recibe_403(monkeypatch):
    """Dar clase en el curso no basta: abre las notas de las demás materias."""
    conexion = ConexionFalsa(CursorFalso([None]))
    monkeypatch.setattr(permissions, "get_connection", lambda: conexion)

    with pytest.raises(HTTPException) as error:
        permissions.require_director_de_curso(5, {"id": 9, "rol": "profesor"})

    assert error.value.status_code == 403
    assert conexion.cerrada is True


def test_otro_rol_recibe_403_sin_consultar(monkeypatch):
    def no_debe(*_):
        raise AssertionError("Un rol desconocido no consulta la base")

    monkeypatch.setattr(permissions, "get_connection", no_debe)
    with pytest.raises(HTTPException) as error:
        permissions.require_director_de_curso(5, {"id": 2, "rol": "super_admin"})
    assert error.value.status_code == 403


def test_con_cursor_prestado_no_pide_otra_conexion(monkeypatch):
    def no_debe(*_):
        raise AssertionError("Con cursor prestado no se abre otra conexión")

    monkeypatch.setattr(permissions, "get_connection", no_debe)
    cursor = CursorFalso([(1,)])
    permissions.require_director_de_curso(5, DIRECTOR, cursor=cursor)
    assert cursor.llamadas[0][1] == (5, 7)

    with pytest.raises(HTTPException) as error:
        permissions.require_director_de_curso(5, DIRECTOR, cursor=CursorFalso([None]))
    assert error.value.status_code == 403


# ---------------------------------------------------------------------------
# Armado del ranking (puro)
# ---------------------------------------------------------------------------

CURSO = {"id": 5, "nombre": "QUINTO A", "jornada": "Mañana", "nivel": "primaria"}
MATERIAS = [
    {"asignacion_id": 55, "materia": "LENGUAJE", "profesor_nombre": "Lina",
     "profesor_apellido": "Torres", "orden_boletin": 1, "tiene_desarrollo": False},
    {"asignacion_id": 60, "materia": "INGLÉS", "profesor_nombre": "Raúl",
     "profesor_apellido": None, "orden_boletin": 2, "tiene_desarrollo": False},
]
ESTUDIANTES = [
    {"estudiante_id": 101, "nombre": "Ana", "apellido": "Pérez",
     "promedio": Decimal("4.6500"), "puesto": 1, "total_rankeados": 2},
    {"estudiante_id": 102, "nombre": "Bruno", "apellido": "Gil",
     "promedio": Decimal("3.2"), "puesto": 2, "total_rankeados": 2},
    {"estudiante_id": 103, "nombre": "Carla", "apellido": "Ruiz",
     "promedio": None, "puesto": None, "total_rankeados": 2},
]
DEFINITIVAS = [
    {"estudiante_id": 101, "asignacion_id": 55, "definitiva_guardada": Decimal("4.80"),
     "guardada": True, "promedio_planilla": Decimal("4.1")},
    {"estudiante_id": 101, "asignacion_id": 60, "definitiva_guardada": Decimal("4.50"),
     "guardada": True, "promedio_planilla": None},
    # Guardada en 0: el boletin la trata como ausente y usa la planilla.
    {"estudiante_id": 102, "asignacion_id": 55, "definitiva_guardada": Decimal("0"),
     "guardada": True, "promedio_planilla": Decimal("3.4")},
    # Sin guardar: sale la de la planilla, marcada como no guardada.
    {"estudiante_id": 103, "asignacion_id": 55, "definitiva_guardada": None,
     "guardada": False, "promedio_planilla": Decimal("2.95")},
    # De alguien que ya no está activo en el curso: no sale.
    {"estudiante_id": 999, "asignacion_id": 55, "definitiva_guardada": Decimal("5"),
     "guardada": True, "promedio_planilla": None},
]
INASISTENCIAS = [{"estudiante_id": 102, "del_periodo": 3, "del_anio": 7}]
OBSERVACIONES = [{"estudiante_id": 101, "texto": "Gran periodo, sigue así."}]


def test_arma_el_ranking_con_las_reglas_del_boletin():
    resultado = controlador.armar_mi_curso(
        CURSO, 2, MATERIAS, ESTUDIANTES, DEFINITIVAS, INASISTENCIAS, OBSERVACIONES
    )

    assert resultado["curso"] == {"id": 5, "nombre": "QUINTO A", "jornada": "Mañana", "nivel": "primaria"}
    assert resultado["periodo"] == 2
    assert resultado["total_rankeados"] == 2
    assert resultado["materias"] == [
        {"asignacion_id": 55, "materia": "LENGUAJE", "profesor": "Lina Torres",
         "tipo_evaluacion": "numerica", "guardados": 2, "total": 3},
        {"asignacion_id": 60, "materia": "INGLÉS", "profesor": "Raúl",
         "tipo_evaluacion": "numerica", "guardados": 1, "total": 3},
    ]

    ana, bruno, carla = resultado["estudiantes"]
    assert ana == {
        "estudiante_id": 101, "nombre": "Ana", "apellido": "Pérez",
        "puesto": 1, "promedio": 4.65,
        "notas": {
            "55": {"definitiva": 4.8, "guardada": True},
            "60": {"definitiva": 4.5, "guardada": True},
        },
        "inasistencias": {"periodo": 0, "anio": 0},
        "observacion_general": "Gran periodo, sigue así.",
    }
    assert bruno["observacion_general"] == ""
    assert bruno["notas"]["55"] == {"definitiva": 3.4, "guardada": True}
    assert bruno["notas"]["60"] == {"definitiva": None, "guardada": False}
    assert bruno["inasistencias"] == {"periodo": 3, "anio": 7}
    assert carla["puesto"] is None and carla["promedio"] is None
    assert carla["notas"]["55"] == {"definitiva": 2.95, "guardada": False}


def test_en_preescolar_las_materias_son_de_caritas():
    preescolar = {**CURSO, "nivel": "preescolar"}
    resultado = controlador.armar_mi_curso(preescolar, 1, MATERIAS[:1], ESTUDIANTES[:1], [], [])
    assert resultado["materias"][0]["tipo_evaluacion"] == "desarrollo"


def test_un_curso_sin_nivel_toma_el_tipo_de_lo_guardado():
    sin_nivel = {**CURSO, "nivel": None}
    con_caritas = [{**MATERIAS[0], "tiene_desarrollo": True}]
    resultado = controlador.armar_mi_curso(sin_nivel, 1, con_caritas, ESTUDIANTES[:1], [], [])
    assert resultado["materias"][0]["tipo_evaluacion"] == "desarrollo"


def test_curso_sin_estudiantes():
    resultado = controlador.armar_mi_curso(CURSO, 1, MATERIAS, [], [], [])
    assert resultado["estudiantes"] == []
    assert resultado["total_rankeados"] == 0
    assert [m["total"] for m in resultado["materias"]] == [0, 0]


# ---------------------------------------------------------------------------
# Lectura: número fijo de consultas
# ---------------------------------------------------------------------------


def test_el_curso_entero_sale_en_seis_consultas(monkeypatch):
    """Ni una por estudiante ni una por materia: con 3 o con 40 estudiantes,
    son las mismas seis idas a la base (la sexta, desde el paso 3, las
    observaciones generales)."""
    cursor = CursorFalso([CURSO, MATERIAS, ESTUDIANTES, DEFINITIVAS, INASISTENCIAS, OBSERVACIONES])
    pedidos = doblar_get_cursor(monkeypatch, cursor)

    resultado = controlador.obtener_mi_curso_controller(5, 2)

    assert len(cursor.llamadas) == 6
    assert pedidos[0]["commit"] is False
    assert cursor.llamadas[0][1] == (5,)
    assert cursor.llamadas[1][1] == (5, 2, NOMBRE_MATERIA_ASISTENCIA_JORNADA)
    assert cursor.llamadas[2][1] == (5, 2, 2, 5)
    assert cursor.llamadas[3][1] == ([55, 60], 2, [55, 60], 2)
    assert cursor.llamadas[4][1] == (2, 5)
    assert cursor.llamadas[5][1] == (5, 2)
    assert [e["estudiante_id"] for e in resultado["estudiantes"]] == [101, 102, 103]
    assert resultado["estudiantes"][0]["observacion_general"] == "Gran periodo, sigue así."


def test_un_curso_que_no_es_del_anio_activo_no_sigue_consultando(monkeypatch):
    cursor = CursorFalso([None])
    doblar_get_cursor(monkeypatch, cursor)

    assert controlador.obtener_mi_curso_controller(5, 2) is None
    assert len(cursor.llamadas) == 1


def test_sin_materias_no_pide_definitivas(monkeypatch):
    cursor = CursorFalso([CURSO, [], ESTUDIANTES, INASISTENCIAS, []])
    doblar_get_cursor(monkeypatch, cursor)

    resultado = controlador.obtener_mi_curso_controller(5, 1)

    assert len(cursor.llamadas) == 5
    assert resultado["materias"] == []
    assert resultado["estudiantes"][1]["inasistencias"] == {"periodo": 3, "anio": 7}


def test_todas_las_lecturas_son_del_anio_activo():
    """Ninguna lectura del curso puede mezclar otro año."""
    from inspect import getsource

    from app.repositories import director_grupo_repository as repositorio

    for funcion in (
        repositorio.leer_cursos_dirigidos,
        repositorio.leer_curso,
        repositorio.leer_estudiantes_con_puesto,
        repositorio.leer_inasistencias_del_curso,
        repositorio.leer_observaciones_del_curso,
        repositorio.estudiante_activo_en_curso,
        repositorio.guardar_observacion_general,
        repositorio.borrar_observacion_general,
    ):
        assert "ANIO_ACTIVO_ID_SQL" in getsource(funcion), funcion.__name__


def test_los_cursos_dirigidos_del_admin_son_una_lista_vacia(monkeypatch):
    def no_debe(*_args, **_kwargs):
        raise AssertionError("El admin no consulta sus cursos dirigidos")

    monkeypatch.setattr(controlador, "get_cursor", no_debe)
    assert controlador.listar_cursos_dirigidos_controller(ADMIN) == []


def test_los_cursos_dirigidos_del_profesor(monkeypatch):
    cursor = CursorFalso([[{"id": 5, "nombre": "QUINTO A", "jornada": "Mañana", "nivel": None}]])
    doblar_get_cursor(monkeypatch, cursor)

    assert controlador.listar_cursos_dirigidos_controller(DIRECTOR) == [
        {"id": 5, "nombre": "QUINTO A", "jornada": "Mañana", "nivel": None}
    ]
    assert cursor.llamadas[0][1] == (7,)


# ---------------------------------------------------------------------------
# Rutas, por la interfaz ASGI real
# ---------------------------------------------------------------------------


def peticion(aplicacion, metodo, ruta):
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


@pytest.fixture
def app_como(monkeypatch):
    """La app real con el usuario que se pida; el controlador va doblado."""
    from app.dependencies import get_current_user
    from app.main import app

    llamadas = []

    def preparar(usuario, resultado=None, error=None):
        app.dependency_overrides[get_current_user] = lambda: usuario

        def falso(*args):
            llamadas.append(args)
            if error is not None:
                raise error
            return resultado

        monkeypatch.setattr(rutas, "obtener_mi_curso_controller", falso)
        monkeypatch.setattr(rutas, "listar_cursos_dirigidos_controller", falso)
        return app

    try:
        yield preparar, llamadas
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_la_proteccion_vive_en_el_router():
    from app.dependencies import get_current_user

    assert get_current_user in [d.dependency for d in rutas.router.dependencies]


def test_el_director_ve_su_curso(app_como, monkeypatch):
    preparar, llamadas = app_como
    monkeypatch.setattr(permissions, "get_connection", lambda: ConexionFalsa(CursorFalso([(1,)])))
    app = preparar(DIRECTOR, resultado={"curso": {"id": 5}, "estudiantes": []})

    status, cuerpo = peticion(app, "GET", "/director-grupo/cursos/5/2")

    assert status == 200
    assert cuerpo == {"curso": {"id": 5}, "estudiantes": []}
    assert llamadas == [(5, 2)]


def test_un_profesor_que_no_dirige_recibe_403_y_no_se_lee_nada(app_como, monkeypatch):
    preparar, llamadas = app_como
    monkeypatch.setattr(permissions, "get_connection", lambda: ConexionFalsa(CursorFalso([None])))
    app = preparar({"id": 9, "rol": "profesor"}, resultado={"no": "debe salir"})

    status, cuerpo = peticion(app, "GET", "/director-grupo/cursos/5/2")

    assert status == 403
    assert cuerpo == {"detail": "No autorizado"}
    assert llamadas == []


def test_el_admin_recibe_404_si_el_curso_no_es_del_anio_activo(app_como):
    preparar, _ = app_como
    app = preparar(ADMIN, resultado=None)

    status, cuerpo = peticion(app, "GET", "/director-grupo/cursos/5/2")

    assert status == 404
    assert cuerpo == {"detail": "Curso no encontrado"}


@pytest.mark.parametrize("ruta", ["/director-grupo/cursos/5/0", "/director-grupo/cursos/5/5", "/director-grupo/cursos/0/1"])
def test_periodo_y_curso_fuera_de_rango_son_422(app_como, ruta):
    preparar, llamadas = app_como
    app = preparar(ADMIN, resultado={})

    status, _ = peticion(app, "GET", ruta)

    assert status == 422
    assert llamadas == []


def test_un_error_inesperado_no_filtra_detalles(app_como):
    preparar, _ = app_como
    app = preparar(ADMIN, error=RuntimeError("relation does not exist"))

    status, cuerpo = peticion(app, "GET", "/director-grupo/cursos/5/2")

    assert status == 500
    assert cuerpo == {"detail": "No se pudo cargar el curso"}


def test_mis_cursos(app_como):
    preparar, llamadas = app_como
    app = preparar(DIRECTOR, resultado=[{"id": 5, "nombre": "QUINTO A"}])

    status, cuerpo = peticion(app, "GET", "/director-grupo/cursos")

    assert status == 200
    assert cuerpo == [{"id": 5, "nombre": "QUINTO A"}]
    assert llamadas == [(DIRECTOR,)]


# ---------------------------------------------------------------------------
# Paso 3: la observación general
# ---------------------------------------------------------------------------

from pydantic import ValidationError  # noqa: E402

from app.schemas.director_grupo import ObservacionGeneralIn  # noqa: E402


def test_el_texto_se_limpia_y_tiene_maximo_500_caracteres():
    assert ObservacionGeneralIn(texto="  Muy bien.\r\nSigue así.  ").texto == "Muy bien.\nSigue así."
    assert ObservacionGeneralIn(texto=None).texto == ""
    assert ObservacionGeneralIn().texto == ""
    # Los espacios de los bordes no cuentan.
    assert len(ObservacionGeneralIn(texto="  " + "a" * 500 + "  ").texto) == 500
    with pytest.raises(ValidationError):
        ObservacionGeneralIn(texto="a" * 501)


def test_guarda_o_reemplaza_con_quien_la_escribio(monkeypatch):
    from datetime import datetime, timezone

    cuando = datetime(2026, 11, 7, 15, 30, tzinfo=timezone.utc)
    cursor = CursorFalso([(1,), {"texto": "Muy bien.", "actualizado_en": cuando}])
    pedidos = doblar_get_cursor(monkeypatch, cursor)

    resultado = controlador.guardar_observacion_general_controller(5, 2, 101, "Muy bien.", DIRECTOR)

    assert pedidos[0]["commit"] is True
    assert cursor.llamadas[0][1] == (101, 5)
    sql, params = cursor.llamadas[1]
    assert "ON CONFLICT (estudiante_id, anio_lectivo_id, periodo)" in sql
    assert params == (101, 2, "Muy bien.", "profesor", 7)
    assert resultado == {
        "estudiante_id": 101,
        "periodo": 2,
        "texto": "Muy bien.",
        "actualizado_en": "2026-11-07T15:30:00+00:00",
    }


def test_un_texto_vacio_borra_la_observacion(monkeypatch):
    cursor = CursorFalso([(1,)])
    doblar_get_cursor(monkeypatch, cursor)

    resultado = controlador.guardar_observacion_general_controller(5, 2, 101, "", ADMIN)

    assert len(cursor.llamadas) == 2
    assert cursor.llamadas[1][0].strip().startswith("DELETE FROM boletin_observacion_general")
    assert cursor.llamadas[1][1] == (101, 2)
    assert resultado["texto"] == "" and resultado["actualizado_en"] is None


def test_no_se_escribe_la_de_un_estudiante_de_otro_curso(monkeypatch):
    """Dirigir un curso no deja escribir en otro."""
    cursor = CursorFalso([None])
    doblar_get_cursor(monkeypatch, cursor)

    with pytest.raises(controlador.EstudianteFueraDelCursoError):
        controlador.guardar_observacion_general_controller(5, 2, 999, "Hola", DIRECTOR)
    assert len(cursor.llamadas) == 1


def peticion_con_cuerpo(aplicacion, metodo, ruta, cuerpo):
    crudo = json.dumps(cuerpo).encode()
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
            (b"content-type", b"application/json"),
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

    asyncio.run(aplicacion(scope, receive, send))
    return salida["status"], json.loads(salida["body"].decode())


RUTA_OBSERVACION = "/director-grupo/cursos/5/2/observaciones/101"


@pytest.fixture
def app_para_guardar(monkeypatch):
    from app.dependencies import get_current_user
    from app.main import app

    llamadas = []

    def preparar(usuario, resultado=None, error=None):
        app.dependency_overrides[get_current_user] = lambda: usuario

        def falso(*args):
            llamadas.append(args)
            if error is not None:
                raise error
            return resultado

        monkeypatch.setattr(rutas, "guardar_observacion_general_controller", falso)
        return app

    try:
        yield preparar, llamadas
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_el_director_guarda_la_observacion(app_para_guardar, monkeypatch):
    preparar, llamadas = app_para_guardar
    monkeypatch.setattr(permissions, "get_connection", lambda: ConexionFalsa(CursorFalso([(1,)])))
    app = preparar(DIRECTOR, resultado={"estudiante_id": 101, "texto": "Bien"})

    status, cuerpo = peticion_con_cuerpo(app, "PUT", RUTA_OBSERVACION, {"texto": "  Bien  "})

    assert status == 200
    assert cuerpo == {"estudiante_id": 101, "texto": "Bien"}
    assert llamadas == [(5, 2, 101, "Bien", DIRECTOR)]


def test_un_profesor_que_no_dirige_no_puede_escribir(app_para_guardar, monkeypatch):
    preparar, llamadas = app_para_guardar
    monkeypatch.setattr(permissions, "get_connection", lambda: ConexionFalsa(CursorFalso([None])))
    app = preparar({"id": 9, "rol": "profesor"}, resultado={})

    status, _ = peticion_con_cuerpo(app, "PUT", RUTA_OBSERVACION, {"texto": "Hola"})

    assert status == 403
    assert llamadas == []


def test_estudiante_de_otro_curso_es_404(app_para_guardar):
    preparar, _ = app_para_guardar
    app = preparar(ADMIN, error=controlador.EstudianteFueraDelCursoError("x"))

    status, cuerpo = peticion_con_cuerpo(app, "PUT", RUTA_OBSERVACION, {"texto": "Hola"})

    assert status == 404
    assert cuerpo == {"detail": "El estudiante no está en este curso"}


def test_mas_de_500_caracteres_es_422_sin_guardar(app_para_guardar):
    preparar, llamadas = app_para_guardar
    app = preparar(ADMIN, resultado={})

    status, _ = peticion_con_cuerpo(app, "PUT", RUTA_OBSERVACION, {"texto": "a" * 501})

    assert status == 422
    assert llamadas == []


def test_un_error_al_guardar_no_filtra_detalles(app_para_guardar):
    preparar, _ = app_para_guardar
    app = preparar(ADMIN, error=RuntimeError("relation does not exist"))

    status, cuerpo = peticion_con_cuerpo(app, "PUT", RUTA_OBSERVACION, {"texto": "Hola"})

    assert status == 500
    assert cuerpo == {"detail": "No se pudo guardar la observación"}

