"""Fase 3 del año lectivo, lecturas por año.

Ver `docs/funcionalidades/ANIO_LECTIVO.md`. Sin base de datos: dobles de
cursor, como el resto de pruebas del año lectivo. Las rutas se conducen por la
aplicacion real (ASGI), como en `test_listas_seguimiento_routes.py`, porque
el codigo de estado y la proteccion solo se ven al pasar por HTTP.

Paso 3.1, los años lectivos y la regla del año pedido. Todo era nuevo; se
fija:

- que años ve cada rol (decisiones 3 y 4);
- que sin año pedido no se gasta ninguna consulta, porque es el camino de
  todas las peticiones de hoy;
- que un profesor no puede pedir otro año y que un año inexistente se
  rechaza.

Paso 3.2, profesor y horarios solo del año (al final del archivo). Con el año
activo, las consultas conservan sus parametros y su numero: lo vigilan las
pruebas que ya existian, que no se tocaron salvo dos dobles de ruta.
"""
import asyncio
import json
from contextlib import contextmanager

import pytest

from app.controllers import anios_lectivos_controller as controlador
from app.controllers import asignacion_controller
from app.repositories import asignaciones_repository, dashboard_repository
from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL, condicion_anio
from app.routes import anios_lectivos as rutas
from app.routes import asignaciones as rutas_asignaciones
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
    ruta, _, consulta = ruta.partition("?")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": ruta,
        "raw_path": ruta.encode(),
        "query_string": consulta.encode(),
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


# ===========================================================================
# Paso 3.2: profesor y horarios, solo del año.
# ===========================================================================


def _normalizar(sql):
    return " ".join(sql.split())


SOLO_EL_ACTIVO = _normalizar(f"c.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}")
SOLO_EL_PEDIDO = "c.anio_lectivo_id = %s"


class CursorQueAnota:
    """Anota cada consulta (con el SQL normalizado) y sirve respuestas en orden."""

    def __init__(self, una=(), todas=()):
        self.consultas = []
        self._una = list(una)
        self._todas = list(todas)

    def execute(self, sql, params=None):
        self.consultas.append((_normalizar(sql), params))

    def fetchone(self):
        return self._una.pop(0) if self._una else None

    def fetchall(self):
        return self._todas.pop(0) if self._todas else []

    def close(self):
        pass


class ConexionFalsa:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self, *args, **kwargs):
        return self._cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def test_condicion_anio_sin_anio_es_el_activo_y_no_lleva_parametros():
    assert condicion_anio("c.anio_lectivo_id") == (
        f"c.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}",
        (),
    )


def test_condicion_anio_con_anio_lo_pasa_como_parametro():
    assert condicion_anio("c.anio_lectivo_id", 5) == ("c.anio_lectivo_id = %s", (5,))


# ---------------------------------------------------------------------------
# Lo que ve el profesor: siempre el año activo, con los parametros de antes.
# ---------------------------------------------------------------------------


def test_mis_clases_son_solo_las_del_anio_activo(monkeypatch):
    cursor = CursorQueAnota()

    @contextmanager
    def get_cursor_falso(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(rutas_asignaciones, "get_cursor", get_cursor_falso)

    rutas_asignaciones.obtener_clases_profesor(profesor_id=7, current_user=PROFESOR)

    [(sql, params)] = cursor.consultas
    assert SOLO_EL_ACTIVO in sql
    assert params == (7,)


def test_los_cursos_del_profesor_son_solo_los_del_anio_activo():
    cursor = CursorQueAnota()

    asignaciones_repository.leer_cursos_de_profesor(cursor, 7)

    [(sql, params)] = cursor.consultas
    assert SOLO_EL_ACTIVO in sql
    assert params == (7,)


def test_las_faltas_del_inicio_del_profesor_son_solo_del_anio_activo():
    cursor = CursorQueAnota()

    dashboard_repository.leer_inasistencias_por_curso(cursor, 7)

    [(sql, params)] = cursor.consultas
    assert SOLO_EL_ACTIVO in sql
    assert params == (7,)


# ---------------------------------------------------------------------------
# Choques de horario: solo entre clases del mismo año.
# ---------------------------------------------------------------------------

# El filtro que la base simulada reconoce, escrito aqui a proposito: si el SQL
# cambia, esta prueba se entera.
FILTRO_DEL_MISMO_ANIO = _normalizar("""
    AND curso_id IN (
        SELECT id FROM cursos
        WHERE anio_lectivo_id = (SELECT anio_lectivo_id FROM cursos WHERE id = %s)
    )
""")

# Cursos y su año: 4 y 5 son de 2026 (año 1); 40 y 41, de 2027 (año 2).
ANIO_DE_CURSO = {4: 1, 5: 1, 40: 2, 41: 2}

# (id, profesor_id, curso_id, dia, inicio, fin)
CLASES_DE_DOS_ANIOS = [
    (1, 9, 4, "Lunes", "08:00", "09:00"),   # 2026
    (2, 9, 41, "Lunes", "10:00", "11:00"),  # 2027
]


class BaseDeHorarios:
    """Contesta las dos lecturas de cruce como lo haria PostgreSQL.

    Filtra por profesor o curso, dia y la clase que se edita. Y, **solo si la
    consulta trae el filtro del año**, deja las clases de cursos del mismo año
    que el curso del ultimo parametro.
    """

    def __init__(self, clases=CLASES_DE_DOS_ANIOS):
        self.clases = clases
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        columna = 1 if "WHERE profesor_id = %s" in sql else 2
        valor, dia = params[0], params[1]
        filas = [c for c in self.clases if c[columna] == valor and c[3] == dia]
        if "AND id != %s" in sql:
            filas = [c for c in filas if c[0] != params[2]]
        if FILTRO_DEL_MISMO_ANIO in sql:
            anio = ANIO_DE_CURSO[params[-1]]
            filas = [c for c in filas if ANIO_DE_CURSO[c[2]] == anio]
        self._filas = [(c[4], c[5]) for c in filas]

    def fetchall(self):
        return self._filas


def test_una_clase_de_2026_no_choca_con_una_de_2027_del_mismo_profesor():
    """El hallazgo 1 del inventario: sin esto, la carga de 2027 no se podria armar."""
    base = BaseDeHorarios()

    assert asignacion_controller.verificar_cruce_horario(
        base, "profesor_id", 9, "Lunes", "08:00", "09:00", 40
    ) is False


def test_dentro_de_2027_el_cruce_del_profesor_se_sigue_detectando():
    base = BaseDeHorarios()

    assert asignacion_controller.verificar_cruce_horario(
        base, "profesor_id", 9, "Lunes", "10:30", "11:30", 40
    ) is True


def test_dentro_de_2026_el_cruce_del_profesor_sigue_igual():
    base = BaseDeHorarios()

    assert asignacion_controller.verificar_cruce_horario(
        base, "profesor_id", 9, "Lunes", "08:30", "09:30", 5
    ) is True


def test_el_cruce_por_curso_sigue_igual():
    base = BaseDeHorarios()

    assert asignacion_controller.verificar_cruce_horario(
        base, "curso_id", 4, "Lunes", "08:30", "09:30", 4
    ) is True
    assert asignacion_controller.verificar_cruce_horario(
        base, "curso_id", 5, "Lunes", "08:30", "09:30", 5
    ) is False


def test_al_editar_tambien_cuentan_solo_las_clases_del_anio_del_curso():
    base = BaseDeHorarios()

    # La de 2026 no choca con una clase de 2027 que se edita.
    assert asignacion_controller.verificar_cruce_horario_editar(
        base, "profesor_id", 9, "Lunes", "08:00", "09:00", 99, 40
    ) is False
    # Dentro de 2027 si, salvo con la misma clase que se esta editando.
    assert asignacion_controller.verificar_cruce_horario_editar(
        base, "profesor_id", 9, "Lunes", "10:30", "11:30", 99, 40
    ) is True
    assert asignacion_controller.verificar_cruce_horario_editar(
        base, "profesor_id", 9, "Lunes", "10:30", "11:30", 2, 40
    ) is False


def _clase(**cambios):
    datos = {
        "profesor_id": 9,
        "curso_id": 4,
        "materia_id": 3,
        "dia": "Lunes",
        "hora_inicio": "08:00",
        "hora_fin": "09:00",
    }
    datos.update(cambios)
    return datos


def test_crear_una_clase_busca_los_cruces_en_el_anio_de_su_curso(monkeypatch):
    """Las respuestas son las del camino feliz de
    `test_asignaciones_estudiantes_caracterizacion.py` (13 consultas)."""
    from app.schemas.asignacion import AsignacionCreate

    cursor = CursorQueAnota(
        una=[(1,), (1,), (1,), None, None, None, (100,), ("Mañana",), ("Matemáticas",), (77,)],
        todas=[[], []],
    )
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: ConexionFalsa(cursor))

    asignacion_controller.asignar_profesor_controller(AsignacionCreate(**_clase()))

    cruces = [params for sql, params in cursor.consultas if FILTRO_DEL_MISMO_ANIO in sql]
    assert cruces == [(9, "Lunes", 4), (4, "Lunes", 4)]
    assert len(cursor.consultas) == 13


def test_editar_una_clase_busca_los_cruces_en_el_anio_de_su_curso(monkeypatch):
    """Las respuestas son las de `test_editar_permite_cambiar_solo_el_horario_con_historial`."""
    from app.schemas.asignacion import AsignacionEdit

    cursor = CursorQueAnota(
        una=[(9, 4, 3, True, 7), (1,), (1,), (1,), None, None, ("Mañana",), ("Matemáticas",), (55,)],
        todas=[[], []],
    )
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: ConexionFalsa(cursor))

    asignacion_controller.editar_asignacion_controller(
        55, AsignacionEdit(**_clase(hora_inicio="10:00", hora_fin="11:00"))
    )

    cruces = [params for sql, params in cursor.consultas if FILTRO_DEL_MISMO_ANIO in sql]
    assert cruces == [(9, "Lunes", 55, 4), (4, "Lunes", 55, 4)]
    assert len(cursor.consultas) == 11


def test_el_cruce_sigue_costando_una_consulta():
    base = BaseDeHorarios()

    asignacion_controller.verificar_cruce_horario(
        base, "profesor_id", 9, "Lunes", "08:00", "09:00", 40
    )

    [(sql, params)] = base.consultas
    assert FILTRO_DEL_MISMO_ANIO in sql
    assert params == (9, "Lunes", 40)


# ---------------------------------------------------------------------------
# Listados del admin: el año pedido o, sin el, el activo.
# ---------------------------------------------------------------------------

LISTADOS_DEL_ADMIN = [
    asignaciones_repository.leer_horarios_admin,
    asignaciones_repository.leer_todas_las_asignaciones,
]


@pytest.mark.parametrize("leer", LISTADOS_DEL_ADMIN)
def test_los_listados_del_admin_sin_anio_son_del_activo_y_sin_parametros(leer):
    cursor = CursorQueAnota()

    leer(cursor)

    [(sql, params)] = cursor.consultas
    assert SOLO_EL_ACTIVO in sql
    assert params is None


@pytest.mark.parametrize("leer", LISTADOS_DEL_ADMIN)
def test_los_listados_del_admin_con_anio_son_de_ese_anio(leer):
    cursor = CursorQueAnota()

    leer(cursor, 5)

    [(sql, params)] = cursor.consultas
    assert SOLO_EL_PEDIDO in sql
    assert ANIO_ACTIVO_ID_SQL not in sql
    assert params == (5,)


def _paginado(monkeypatch, **kwargs):
    cursor = CursorQueAnota(una=[(5, 2027, "preparacion"), (0,)])
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: ConexionFalsa(cursor))
    asignacion_controller.obtener_todas_asignaciones_paginado_controller(
        limit=10, offset=20, profesor_id=3, **kwargs
    )
    return cursor.consultas


def test_el_paginado_sin_anio_conserva_sus_dos_consultas_y_parametros(monkeypatch):
    conteo, pagina = _paginado(monkeypatch)

    assert SOLO_EL_ACTIVO in conteo[0]
    assert conteo[1] == [3]
    assert pagina[1] == [3, 10, 20]


def test_el_paginado_con_anio_lo_valida_y_lo_pasa_antes_de_limit(monkeypatch):
    anio, conteo, pagina = _paginado(monkeypatch, anio_lectivo_id=5)

    assert anio == (SQL_POR_ID, (5,))
    assert SOLO_EL_PEDIDO in conteo[0]
    assert conteo[1] == [3, 5]
    assert pagina[1] == [3, 5, 10, 20]


def _disponibilidad(monkeypatch, cursor, **kwargs):
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: ConexionFalsa(cursor))
    return asignacion_controller.obtener_disponibilidad_profesor_controller(3, "Lunes", **kwargs)


def test_la_disponibilidad_sin_anio_cuenta_las_clases_del_activo(monkeypatch):
    cursor = CursorQueAnota()

    _disponibilidad(monkeypatch, cursor, excluir_asignacion_id=8)

    [(sql, params)] = cursor.consultas
    assert _normalizar(
        f"curso_id IN (SELECT id FROM cursos WHERE anio_lectivo_id = {ANIO_ACTIVO_ID_SQL})"
    ) in sql
    assert params == [3, "Lunes", 8]


def test_la_disponibilidad_con_anio_cuenta_las_clases_de_ese_anio(monkeypatch):
    cursor = CursorQueAnota(una=[(5, 2027, "preparacion")])

    _disponibilidad(monkeypatch, cursor, excluir_asignacion_id=8, anio_lectivo_id=5)

    anio, (sql, params) = cursor.consultas
    assert anio == (SQL_POR_ID, (5,))
    assert "curso_id IN (SELECT id FROM cursos WHERE anio_lectivo_id = %s)" in sql
    assert params == [3, "Lunes", 8, 5]


CONTROLADORES_DEL_ADMIN_CON_ANIO = {
    "todas": lambda: asignacion_controller.obtener_todas_asignaciones_controller(
        anio_lectivo_id=99
    ),
    "horarios": lambda: asignacion_controller.obtener_horarios_admin_controller(
        anio_lectivo_id=99
    ),
    "paginado": lambda: asignacion_controller.obtener_todas_asignaciones_paginado_controller(
        limit=10, anio_lectivo_id=99
    ),
    "disponibilidad": lambda: asignacion_controller.obtener_disponibilidad_profesor_controller(
        3, "Lunes", anio_lectivo_id=99
    ),
}


@pytest.mark.parametrize("nombre", sorted(CONTROLADORES_DEL_ADMIN_CON_ANIO))
def test_un_anio_que_no_existe_no_llega_a_consultar_el_listado(monkeypatch, nombre):
    cursor = CursorQueAnota()

    @contextmanager
    def get_cursor_falso(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(asignacion_controller, "get_cursor", get_cursor_falso)
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: ConexionFalsa(cursor))

    with pytest.raises(ValueError, match="El año lectivo seleccionado no existe."):
        CONTROLADORES_DEL_ADMIN_CON_ANIO[nombre]()

    assert cursor.consultas == [(SQL_POR_ID, (99,))]


# ---------------------------------------------------------------------------
# Las tres rutas del admin, por HTTP.
# ---------------------------------------------------------------------------

RUTAS_DEL_ADMIN_CON_ANIO = {
    "/asignaciones/lista": "obtener_todas_asignaciones_controller",
    "/hora/horarios-admin": "obtener_horarios_admin_controller",
    "/profesores/3/disponibilidad?dia=Lunes": "obtener_disponibilidad_profesor_controller",
}


@pytest.fixture
def app_admin_con_controlador(monkeypatch):
    """La app real con un admin y el controlador de la ruta doblado."""
    from app.dependencies import get_current_user
    from app.main import app

    recibido = []

    def doblar(nombre, error=None):
        def falso(*args, **kwargs):
            recibido.append(kwargs.get("anio_lectivo_id"))
            if error is not None:
                raise error
            return []

        monkeypatch.setattr(rutas_asignaciones, nombre, falso)

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app, doblar, recibido
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _con_anio(ruta, anio):
    separador = "&" if "?" in ruta else "?"
    return f"{ruta}{separador}anio_lectivo_id={anio}"


@pytest.mark.parametrize("ruta", sorted(RUTAS_DEL_ADMIN_CON_ANIO))
def test_las_rutas_del_admin_pasan_el_anio_al_controlador(app_admin_con_controlador, ruta):
    app, doblar, recibido = app_admin_con_controlador
    doblar(RUTAS_DEL_ADMIN_CON_ANIO[ruta])

    assert peticion_get(app, ruta)[0] == 200
    assert peticion_get(app, _con_anio(ruta, 5))[0] == 200
    assert recibido == [None, 5]


@pytest.mark.parametrize("ruta", sorted(RUTAS_DEL_ADMIN_CON_ANIO))
def test_las_rutas_del_admin_rechazan_un_anio_no_positivo(app_admin_con_controlador, ruta):
    app, doblar, _ = app_admin_con_controlador
    doblar(RUTAS_DEL_ADMIN_CON_ANIO[ruta])

    assert peticion_get(app, _con_anio(ruta, 0))[0] == 422


@pytest.mark.parametrize("ruta", sorted(RUTAS_DEL_ADMIN_CON_ANIO))
def test_las_rutas_del_admin_responden_404_si_el_anio_no_existe(app_admin_con_controlador, ruta):
    app, doblar, _ = app_admin_con_controlador
    doblar(
        RUTAS_DEL_ADMIN_CON_ANIO[ruta],
        error=ValueError("El año lectivo seleccionado no existe."),
    )

    status, cuerpo = peticion_get(app, _con_anio(ruta, 99))

    assert status == 404
    assert cuerpo == {"detail": "El año lectivo seleccionado no existe."}
