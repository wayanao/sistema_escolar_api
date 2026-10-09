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
from app.controllers import (
    asignacion_controller,
    curso_controller,
    estudiante_controller,
    listas_seguimiento_controller,
    tipos_pagos_controller,
)
from app.repositories import (
    asignaciones_repository,
    dashboard_repository,
    estudiantes_repository,
    listas_seguimiento_repository,
    observador_repository,
)
from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL, condicion_anio
from app.routes import anios_lectivos as rutas
from app.routes import asignaciones as rutas_asignaciones
from app.routes import cursos as rutas_cursos
from app.routes import listas_seguimiento as rutas_listas
from app.routes import tipos_pagos as rutas_tipos_pagos
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
    return peticion(aplicacion, "GET", ruta)


def peticion(aplicacion, metodo, ruta, cuerpo=None):
    """Una peticion HTTP real contra la app. Devuelve (status, cuerpo)."""
    ruta, _, consulta = ruta.partition("?")
    crudo = json.dumps(cuerpo).encode() if cuerpo is not None else b""
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
    """Anota cada consulta (con el SQL normalizado) y sirve respuestas en orden.

    Paso 3.7: la consulta de la guardia de escritura responde "2026 activo"
    sin gastar las respuestas preparadas.
    """

    def __init__(self, una=(), todas=()):
        self.consultas = []
        self._una = list(una)
        self._todas = list(todas)

    def execute(self, sql, params=None):
        self.consultas.append((_normalizar(sql), params))

    def _es_la_guardia(self):
        return bool(self.consultas) and self.consultas[-1][0].startswith(
            "SELECT al.anio, al.estado"
        )

    def fetchone(self):
        if self._es_la_guardia():
            return (2026, "activo")
        return self._una.pop(0) if self._una else None

    def fetchall(self):
        if self._es_la_guardia():
            return [(2026, "activo")]
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
    `test_asignaciones_estudiantes_caracterizacion.py` (13 consultas; 14 con la
    guardia de escritura del paso 3.7)."""
    from app.schemas.asignacion import AsignacionCreate

    cursor = CursorQueAnota(
        una=[(1,), (1,), (1,), None, None, None, (100,), ("Mañana",), ("Matemáticas",), (77,)],
        todas=[[], []],
    )
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: ConexionFalsa(cursor))

    asignacion_controller.asignar_profesor_controller(AsignacionCreate(**_clase()))

    cruces = [params for sql, params in cursor.consultas if FILTRO_DEL_MISMO_ANIO in sql]
    assert cruces == [(9, "Lunes", 4), (4, "Lunes", 4)]
    assert len(cursor.consultas) == 14


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
    # 11, mas la guardia de escritura del paso 3.7.
    assert len(cursor.consultas) == 12


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


# ===========================================================================
# Paso 3.3: cursos y conceptos por año.
# ===========================================================================

# En las bases simuladas, el año 1 es 2026 (activo) y el 2 es 2027.
ANIO_DEL_CURSO_SQL = "anio_lectivo_id = (SELECT anio_lectivo_id FROM cursos WHERE id = %s)"
ANIO_DEL_CONCEPTO_SQL = (
    "anio_lectivo_id = (SELECT anio_lectivo_id FROM tipos_de_pagos WHERE id = %s)"
)
ANIO_ACTIVO_SQL = _normalizar(f"anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}")


class BaseDeCursos:
    """Contesta la consulta de nombre repetido de cursos como PostgreSQL.

    Filtra por nombre, jornada y el curso que se edita; y por año **solo si la
    consulta trae el filtro**: el activo, o el del curso del ultimo parametro.
    """

    def __init__(self, cursos):
        self.cursos = cursos  # (id, nombre, jornada, anio)
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        nombre, jornada, curso_id = params[0], params[1], params[2]
        filas = [
            c for c in self.cursos
            if c[1] == nombre and c[2].lower() == jornada.lower()
            and (curso_id is None or c[0] != curso_id)
        ]
        if ANIO_ACTIVO_SQL in sql:
            filas = [c for c in filas if c[3] == 1]
        elif ANIO_DEL_CURSO_SQL in sql:
            anio = next(c[3] for c in self.cursos if c[0] == params[-1])
            filas = [c for c in filas if c[3] == anio]
        self._filas = [(c[0],) for c in filas]

    def fetchone(self):
        return self._filas[0] if self._filas else None


CURSOS_DE_DOS_ANIOS = [
    (1, "PRIMERO A", "Mañana", 1),
    (3, "SEGUNDO A", "Mañana", 1),
    (2, "PRIMERO B", "Mañana", 2),
    (4, "SEGUNDO B", "Mañana", 2),
]


def test_editar_un_curso_de_2027_con_el_nombre_de_uno_de_2026_no_es_repetido():
    base = BaseDeCursos(CURSOS_DE_DOS_ANIOS)

    curso_controller._validar_curso_unico(base, "PRIMERO A", "Mañana", curso_id=2)


def test_dentro_del_mismo_anio_el_nombre_repetido_se_sigue_rechazando():
    base = BaseDeCursos(CURSOS_DE_DOS_ANIOS)

    with pytest.raises(curso_controller.CursoDuplicadoError):
        curso_controller._validar_curso_unico(base, "PRIMERO A", "Mañana", curso_id=3)
    with pytest.raises(curso_controller.CursoDuplicadoError):
        curso_controller._validar_curso_unico(base, "PRIMERO B", "Mañana", curso_id=4)


def test_un_curso_nuevo_se_compara_con_los_del_anio_activo():
    base = BaseDeCursos(CURSOS_DE_DOS_ANIOS)

    with pytest.raises(curso_controller.CursoDuplicadoError):
        curso_controller._validar_curso_unico(base, "PRIMERO A", "Mañana")
    # "PRIMERO B" solo existe en 2027: en el año activo no es repetido.
    curso_controller._validar_curso_unico(base, "PRIMERO B", "Mañana")


def test_el_nombre_repetido_de_cursos_sigue_costando_una_consulta():
    base = BaseDeCursos(CURSOS_DE_DOS_ANIOS)

    curso_controller._validar_curso_unico(base, "TERCERO A", "Mañana")
    curso_controller._validar_curso_unico(base, "TERCERO A", "Mañana", curso_id=2)

    nuevo, editado = base.consultas
    assert nuevo[1] == ("TERCERO A", "Mañana", None, None)
    assert editado[1] == ("TERCERO A", "Mañana", 2, 2, 2)


def _cursos(monkeypatch, funcion, una=(), **kwargs):
    cursor = CursorQueAnota(una=una)
    monkeypatch.setattr(curso_controller, "get_connection", lambda: ConexionFalsa(cursor))
    funcion(**kwargs)
    return cursor.consultas


def test_la_lista_de_cursos_sin_anio_es_del_activo_y_sin_parametro_nuevo(monkeypatch):
    [(sql, params)] = _cursos(monkeypatch, curso_controller.obtener_cursos_controller)

    assert ANIO_ACTIVO_SQL in sql
    assert params == ["activo"]


def test_la_lista_de_cursos_con_anio_lo_valida_y_lo_usa(monkeypatch):
    anio, (sql, params) = _cursos(
        monkeypatch,
        curso_controller.obtener_cursos_controller,
        una=[(5, 2027, "preparacion")],
        anio_lectivo_id=5,
    )

    assert anio == (SQL_POR_ID, (5,))
    assert "anio_lectivo_id = %s" in sql
    assert ANIO_ACTIVO_ID_SQL not in sql
    assert params == ["activo", 5]


def test_el_paginado_de_cursos_con_anio_lo_pasa_antes_de_limit(monkeypatch):
    anio, conteo, pagina = _cursos(
        monkeypatch,
        curso_controller.obtener_cursos_paginado_controller,
        una=[(5, 2027, "preparacion"), (0,)],
        limit=10,
        offset=20,
        busqueda="pri",
        anio_lectivo_id=5,
    )

    assert anio == (SQL_POR_ID, (5,))
    assert conteo[1] == ["%pri%", "activo", 5]
    assert pagina[1] == ["%pri%", "activo", 5, 10, 20]


# ---------------------------------------------------------------------------
# Conceptos de pago (dinero: zona sensible).
# ---------------------------------------------------------------------------


class BaseDeConceptos:
    """Contesta el nombre repetido de conceptos como PostgreSQL, y las escrituras.

    Para el nombre repetido filtra por nombre (sin mayusculas ni espacios), el
    concepto que se edita y, **solo si la consulta trae el filtro**, el año: el
    activo o el del concepto que se edita.
    """

    def __init__(self, conceptos):
        self.conceptos = conceptos  # (id, nombre, anio)
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        if sql.startswith(("INSERT", "UPDATE")):
            self._filas = [(99,)]
            return
        if sql.startswith("SELECT al.anio, al.estado"):
            # Paso 3.7: la guardia de escritura; aqui, un año editable.
            self._filas = [(2027, "preparacion")]
            return
        nombre = params[0].strip().lower()
        excluido = params[1] if "id <> %s" in sql else None
        filas = [
            c for c in self.conceptos
            if c[1].strip().lower() == nombre and c[0] != excluido
        ]
        if ANIO_ACTIVO_SQL in sql:
            filas = [c for c in filas if c[2] == 1]
        elif ANIO_DEL_CONCEPTO_SQL in sql:
            anio = next(c[2] for c in self.conceptos if c[0] == params[-1])
            filas = [c for c in filas if c[2] == anio]
        self._filas = [(c[0],) for c in filas]

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def close(self):
        pass


# MENSUALIDAD existe en 2026 (1) y su copia en 2027 (2); MATRICULA solo en 2027.
CONCEPTOS_DE_DOS_ANIOS = [
    (1, "MENSUALIDAD", 1),
    (2, "MENSUALIDAD", 2),
    (3, "MATRICULA", 2),
]


def _conceptos(monkeypatch):
    base = BaseDeConceptos(CONCEPTOS_DE_DOS_ANIOS)
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: ConexionFalsa(base))
    return base


def test_la_copia_de_2027_de_un_concepto_puede_llamarse_igual_que_la_de_2026(monkeypatch):
    """Es lo que la copia de conceptos de la fase 5 necesita (decision 17)."""
    _conceptos(monkeypatch)

    assert tipos_pagos_controller.actualizar_tipo_pago(2, "MENSUALIDAD", 0) is True


def test_dentro_de_un_anio_el_nombre_de_concepto_repetido_se_rechaza(monkeypatch):
    base = _conceptos(monkeypatch)

    with pytest.raises(tipos_pagos_controller.TipoPagoDuplicadoError):
        tipos_pagos_controller.actualizar_tipo_pago(3, "mensualidad", 0)
    with pytest.raises(tipos_pagos_controller.TipoPagoDuplicadoError):
        tipos_pagos_controller.crear_tipo_pago("Mensualidad ", 0)
    assert not any(sql.startswith(("INSERT", "UPDATE")) for sql, _ in base.consultas)


def test_un_concepto_nuevo_se_compara_con_los_del_anio_activo(monkeypatch):
    base = _conceptos(monkeypatch)

    # MATRICULA solo existe en 2027: en el año activo no es repetida.
    tipos_pagos_controller.crear_tipo_pago("MATRICULA", 300000)

    duplicado, insercion = base.consultas
    assert ANIO_ACTIVO_SQL in duplicado[0]
    assert duplicado[1] == ("MATRICULA",)
    assert insercion[0].startswith("INSERT INTO tipos_de_pagos")


def test_editar_un_concepto_compara_con_los_de_su_anio(monkeypatch):
    base = _conceptos(monkeypatch)

    tipos_pagos_controller.actualizar_tipo_pago(3, "PENSION", 0)

    # base.consultas[0] es la guardia de escritura del paso 3.7.
    duplicado = base.consultas[1]
    assert ANIO_DEL_CONCEPTO_SQL in duplicado[0]
    assert duplicado[1] == ("PENSION", 3, 3)


@pytest.mark.parametrize(
    ("listar", "sql_esperado"),
    [
        (
            tipos_pagos_controller.listar_tipos_pagos,
            "SELECT id, nombre, valor FROM tipos_de_pagos WHERE anio_lectivo_id = %s ORDER BY nombre",
        ),
        (
            tipos_pagos_controller.listar_tipos_pagos_detallado,
            "SELECT * FROM tipos_de_pagos WHERE anio_lectivo_id = %s ORDER BY nombre",
        ),
    ],
)
def test_los_conceptos_con_anio_son_los_de_ese_anio(monkeypatch, listar, sql_esperado):
    cursor = CursorQueAnota(una=[(5, 2027, "preparacion")])
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: ConexionFalsa(cursor))

    listar(anio_lectivo_id=5)

    assert cursor.consultas[0] == (SQL_POR_ID, (5,))
    assert (sql_esperado, (5,)) in cursor.consultas


class BaseDePrecios:
    """Contesta las consultas de guardar precios por curso, como PostgreSQL.

    La primera dice si el concepto existe y que cursos pedidos son de otro año.
    Solo separa por año **si la consulta trae exactamente esa comparacion**; si
    no, contesta que todos los pedidos lo son, como haria una consulta sin el
    filtro correcto.
    """

    COMPARACION_DE_ANIO = "AND c.anio_lectivo_id <> tp.anio_lectivo_id"

    # curso -> (nombre, anio); concepto -> anio
    CURSOS = {4: ("PRIMERO A", 1), 40: ("PRIMERO A", 2), 41: ("SEGUNDO A", 2)}
    CONCEPTOS = {1: 1, 2: 2}

    def __init__(self):
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        if sql.startswith("SELECT al.anio, al.estado"):
            # Paso 3.7: la guardia de escritura; aqui, un año editable.
            self._filas = [(2027, "preparacion")]
            return
        if "AS cursos_de_otro_anio" in sql:
            curso_ids, concepto = params
            if concepto not in self.CONCEPTOS:
                self._filas = []
                return
            separa_por_anio = self.COMPARACION_DE_ANIO in sql
            nombres = sorted(
                self.CURSOS[c][0] for c in curso_ids
                if not separa_por_anio or self.CURSOS[c][1] != self.CONCEPTOS[concepto]
            )
            self._filas = [{"cursos_de_otro_anio": nombres}]
        elif "information_schema.tables" in sql:
            self._filas = [{"table_name": "tipos_pagos_cursos"}]
        else:
            self._filas = []

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)

    def close(self):
        pass


@pytest.fixture
def precios(monkeypatch):
    base = BaseDePrecios()
    conexion = ConexionQueCuenta(base)
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)
    return base, conexion


class ConexionQueCuenta(ConexionFalsa):
    def __init__(self, cursor):
        super().__init__(cursor)
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _escrituras(base):
    return [sql for sql, _ in base.consultas if sql.startswith(("INSERT", "DELETE"))]


def test_un_concepto_de_2027_acepta_precios_de_cursos_de_2027(precios):
    base, conexion = precios

    resultado = tipos_pagos_controller.upsert_cursos_asignados(
        2, [{"curso_id": 40, "valor": 350000}, {"curso_id": 41, "valor": 350000}]
    )

    assert resultado == []
    assert len(_escrituras(base)) == 3  # un DELETE y dos INSERT
    assert conexion.commits == 1


def test_un_concepto_de_2027_no_acepta_precio_en_un_curso_de_2026(precios):
    base, conexion = precios

    with pytest.raises(tipos_pagos_controller.CursoDeOtroAnioError) as error:
        tipos_pagos_controller.upsert_cursos_asignados(
            2, [{"curso_id": 4, "valor": 350000}, {"curso_id": 40, "valor": 350000}]
        )

    assert str(error.value) == (
        "Estos cursos no son del año lectivo del concepto: PRIMERO A."
    )
    assert _escrituras(base) == []
    assert conexion.rollbacks == 1
    assert conexion.commits == 0


def test_guardar_precios_no_agrega_consultas(precios):
    """La comprobacion de que los cursos son del año del concepto va en la
    misma consulta que ya miraba si el concepto existe: no hay una ida mas a la
    base por ella. La guardia de escritura del paso 3.7 si suma una (aceptado
    por el usuario), y va primero."""
    base, _ = precios

    tipos_pagos_controller.upsert_cursos_asignados(1, [{"curso_id": 4, "valor": 300000}])

    guardia, params_guardia = base.consultas[0]
    assert guardia.startswith("SELECT al.anio, al.estado")
    assert params_guardia == (1,)
    segunda, _params = base.consultas[1]
    assert "FROM tipos_de_pagos tp WHERE tp.id = %s" in segunda
    assert "AS cursos_de_otro_anio" in segunda
    assert not any("SELECT 1 FROM tipos_de_pagos" in sql for sql, _ in base.consultas)
    # Guardia + concepto + DELETE + INSERT + tablas + relectura.
    assert len(base.consultas) == 6


def test_un_concepto_que_no_existe_sigue_respondiendo_none(precios):
    base, _ = precios

    assert tipos_pagos_controller.upsert_cursos_asignados(99, [{"curso_id": 4}]) is None
    assert _escrituras(base) == []


# ---------------------------------------------------------------------------
# Listas de seguimiento: "todos los cursos" son los de un año.
# ---------------------------------------------------------------------------


def test_contar_los_cursos_de_las_listas_sin_anio_es_el_activo():
    cursor = CursorQueAnota(una=[(11,)])

    assert listas_seguimiento_repository.contar_cursos_activos(cursor) == 11

    [(sql, params)] = cursor.consultas
    assert SOLO_EL_ACTIVO in sql
    assert params is None


def test_contar_los_cursos_de_las_listas_con_anio():
    cursor = CursorQueAnota(una=[(4,)])

    listas_seguimiento_repository.contar_cursos_activos(cursor, 5)

    [(sql, params)] = cursor.consultas
    assert SOLO_EL_PEDIDO in sql
    assert params == (5,)


class CursorConFilas(CursorQueAnota):
    rowcount = 3


def test_crear_la_columna_en_todos_los_cursos_sin_anio_es_en_el_activo():
    cursor = CursorConFilas()

    listas_seguimiento_repository.crear_columna_en_cursos_activos(cursor, "Excursion")

    [(sql, params)] = cursor.consultas
    assert sql.endswith(SOLO_EL_ACTIVO)
    assert params == ("Excursion", "Excursion")


def test_crear_la_columna_en_todos_los_cursos_con_anio():
    cursor = CursorConFilas()

    listas_seguimiento_repository.crear_columna_en_cursos_activos(cursor, "Excursion", 5)

    [(sql, params)] = cursor.consultas
    assert sql.endswith(SOLO_EL_PEDIDO)
    assert params == ("Excursion", "Excursion", 5)


def test_el_alta_en_todos_los_cursos_valida_el_anio_y_lo_pasa(monkeypatch):
    cursor = CursorConFilas(una=[(5, 2027, "preparacion"), (4,)])

    @contextmanager
    def get_cursor_falso(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(listas_seguimiento_controller, "get_cursor", get_cursor_falso)

    respuesta = listas_seguimiento_controller.crear_columna_en_todos_los_cursos_controller(
        "Excursion", anio_lectivo_id=5
    )

    anio, alta, conteo = cursor.consultas
    assert anio == (SQL_POR_ID, (5,))
    assert alta[1] == ("Excursion", "Excursion", 5)
    assert conteo[1] == (5,)
    assert respuesta == {"creadas": 3, "omitidas": 1, "total": 4}


def test_el_alta_en_todos_los_cursos_de_un_anio_que_no_existe_no_escribe(monkeypatch):
    cursor = CursorConFilas()

    @contextmanager
    def get_cursor_falso(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(listas_seguimiento_controller, "get_cursor", get_cursor_falso)

    with pytest.raises(ValueError, match="El año lectivo seleccionado no existe."):
        listas_seguimiento_controller.crear_columna_en_todos_los_cursos_controller(
            "Excursion", anio_lectivo_id=99
        )

    assert cursor.consultas == [(SQL_POR_ID, (99,))]


# ---------------------------------------------------------------------------
# Las rutas del paso 3.3, por HTTP.
# ---------------------------------------------------------------------------

# ruta -> (metodo, modulo, controlador, cuerpo)
RUTAS_CON_ANIO_33 = {
    "/cursos": ("GET", rutas_cursos, "obtener_cursos_controller", None),
    "/tipos-pagos": ("GET", rutas_tipos_pagos, "listar_tipos_pagos", None),
    "/tipos-pagos/detallado": ("GET", rutas_tipos_pagos, "listar_tipos_pagos_detallado", None),
    "/listas-seguimiento/columnas-en-todos-los-cursos": (
        "POST",
        rutas_listas,
        "crear_columna_en_todos_los_cursos_controller",
        {"nombre": "Excursion"},
    ),
}


@pytest.fixture
def app_admin_33(monkeypatch):
    from app.dependencies import get_current_user
    from app.main import app

    recibido = []

    def doblar(ruta, error=None):
        _metodo, modulo, nombre, _cuerpo = RUTAS_CON_ANIO_33[ruta]

        def falso(*args, **kwargs):
            recibido.append(kwargs.get("anio_lectivo_id"))
            if error is not None:
                raise error
            return []

        monkeypatch.setattr(modulo, nombre, falso)

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app, doblar, recibido
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _pedir(app, ruta, anio=None):
    metodo, _modulo, _nombre, cuerpo = RUTAS_CON_ANIO_33[ruta]
    destino = ruta if anio is None else _con_anio(ruta, anio)
    return peticion(app, metodo, destino, cuerpo)


@pytest.mark.parametrize("ruta", sorted(RUTAS_CON_ANIO_33))
def test_las_rutas_del_paso_33_pasan_el_anio(app_admin_33, ruta):
    app, doblar, recibido = app_admin_33
    doblar(ruta)

    assert _pedir(app, ruta)[0] == 200
    assert _pedir(app, ruta, 5)[0] == 200
    assert _pedir(app, ruta, 0)[0] == 422
    assert recibido == [None, 5]


@pytest.mark.parametrize("ruta", sorted(RUTAS_CON_ANIO_33))
def test_las_rutas_del_paso_33_responden_404_si_el_anio_no_existe(app_admin_33, ruta):
    app, doblar, _ = app_admin_33
    doblar(ruta, error=ValueError("El año lectivo seleccionado no existe."))

    status, cuerpo = _pedir(app, ruta, 99)

    assert status == 404
    assert cuerpo == {"detail": "El año lectivo seleccionado no existe."}


def test_un_precio_en_un_curso_de_otro_anio_responde_400_con_el_mensaje(app_admin_33, monkeypatch):
    app, _, _ = app_admin_33

    def falso(*args, **kwargs):
        raise tipos_pagos_controller.CursoDeOtroAnioError(
            "Estos cursos no son del año lectivo del concepto: PRIMERO A."
        )

    monkeypatch.setattr(rutas_tipos_pagos, "upsert_cursos_asignados", falso)

    status, cuerpo = peticion(
        app, "PUT", "/tipos-pagos/2/cursos", {"cursos": [{"curso_id": 4, "valor": 1}]}
    )

    assert status == 400
    assert cuerpo == {"detail": "Estos cursos no son del año lectivo del concepto: PRIMERO A."}


# ===========================================================================
# Paso 3.4: estudiantes y cartera desde las matriculas (dinero).
# ===========================================================================

# 2026 cerrado (id 1) y 2027 activo (id 2).
ANIOS_DOS = {1: (1, 2026, "cerrado"), 2: (2, 2027, "activo")}
MATRICULAS_DEL_ANIO = "FROM matriculas WHERE anio_lectivo_id = %s"


class BaseDeEstudiantes:
    """Estudiantes y matriculas de dos años, contestados como PostgreSQL.

    Ana (7) estuvo en el curso 3 en 2026 y esta en el 30 en 2027. Beto (8) es
    nuevo en 2027 (curso 31). Luis (9) estuvo en 2026 (curso 3), se retiro y
    hoy no tiene curso. La lista sale de las matriculas del año **solo si la
    consulta las une**; si no, de `estudiantes.curso_id`.
    """

    ESTUDIANTES = [
        (7, "Ana", "Rios", "1", None, 30, "a@x.co", "activo"),
        (8, "Beto", "Diaz", "2", None, 31, None, "activo"),
        (9, "Luis", "Mora", "3", None, None, None, "retirado"),
    ]
    MATRICULAS = {(7, 1): 3, (9, 1): 3, (7, 2): 30, (8, 2): 31}

    def __init__(self):
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        params = list(params or ())
        if sql == SQL_POR_ID:
            self._filas = [ANIOS_DOS[params[0]]] if params[0] in ANIOS_DOS else []
            return
        filas = list(self.ESTUDIANTES)
        if MATRICULAS_DEL_ANIO in sql:
            anio = params.pop(0)
            # El curso de la matricula solo si la consulta lo pide; si no, el
            # de `estudiantes.curso_id`, como haria PostgreSQL.
            del_anio = "m.curso_del_anio" in sql
            filas = [
                (*e[:5], self.MATRICULAS[(e[0], anio)] if del_anio else e[5], *e[6:])
                for e in filas if (e[0], anio) in self.MATRICULAS
            ]
        if "COALESCE(LOWER(estado), 'activo') = %s" in sql:
            estado = params.pop(0)
            filas = [e for e in filas if e[7] == estado]
        filas.sort(key=lambda e: (e[2], e[1]))
        self._filas = [(len(filas),)] if sql.startswith("SELECT COUNT(*)") else filas

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)

    def close(self):
        pass


def _lista(monkeypatch, **kwargs):
    base = BaseDeEstudiantes()
    monkeypatch.setattr(estudiante_controller, "get_connection", lambda: ConexionFalsa(base))
    respuesta = estudiante_controller.obtener_estudiantes_controller(**kwargs)
    return [(e["id"], e["curso_id"]) for e in respuesta], base.consultas


def test_sin_anio_la_lista_de_estudiantes_es_la_de_siempre(monkeypatch):
    """La usan Pagos y Ventas: tiene que encontrar a cualquiera, como hoy."""
    lista, consultas = _lista(monkeypatch)

    assert lista == [(8, 31), (7, 30)]
    [(sql, params)] = consultas
    assert "matriculas" not in sql
    assert params == ("activo",)


def test_con_el_anio_activo_la_lista_de_estudiantes_es_la_de_siempre(monkeypatch):
    lista, (anio, (sql, params)) = _lista(monkeypatch, anio_lectivo_id=2)

    assert lista == [(8, 31), (7, 30)]
    assert anio == (SQL_POR_ID, (2,))
    assert "matriculas" not in sql
    assert params == ("activo",)


def test_con_otro_anio_la_lista_son_sus_matriculados_con_el_curso_de_ese_anio(monkeypatch):
    lista, (_anio, (sql, params)) = _lista(monkeypatch, estado="todos", anio_lectivo_id=1)

    # Luis se retiro despues, Ana estaba en el curso 3, Beto no estaba.
    assert lista == [(9, 3), (7, 3)]
    assert MATRICULAS_DEL_ANIO in sql
    assert params == (1,)


def test_con_otro_anio_el_filtro_de_estado_sigue_valiendo(monkeypatch):
    lista, (_anio, (_sql, params)) = _lista(monkeypatch, anio_lectivo_id=1)

    assert lista == [(7, 3)]
    assert params == (1, "activo")


def test_el_paginado_de_estudiantes_de_otro_anio_pone_el_anio_primero(monkeypatch):
    base = BaseDeEstudiantes()
    monkeypatch.setattr(estudiante_controller, "get_connection", lambda: ConexionFalsa(base))

    respuesta = estudiante_controller.obtener_estudiantes_paginado_controller(
        limit=10, offset=0, busqueda=None, estado="todos", anio_lectivo_id=1
    )

    _anio, conteo, pagina = base.consultas
    assert MATRICULAS_DEL_ANIO in conteo[0] and MATRICULAS_DEL_ANIO in pagina[0]
    assert conteo[1] == (1,)
    assert pagina[1] == (1, 10, 0)
    assert respuesta["total"] == 2


def test_la_lista_de_un_anio_que_no_existe_no_consulta_estudiantes(monkeypatch):
    base = BaseDeEstudiantes()
    monkeypatch.setattr(estudiante_controller, "get_connection", lambda: ConexionFalsa(base))

    with pytest.raises(ValueError, match="El año lectivo seleccionado no existe."):
        estudiante_controller.obtener_estudiantes_controller(anio_lectivo_id=99)

    assert base.consultas == [(SQL_POR_ID, (99,))]


# ---------------------------------------------------------------------------
# Cartera por año (decisiones 18 y 19).
# ---------------------------------------------------------------------------

# Un concepto "unico" de 300.000 en el curso 3, sin pagar.
CONCEPTO_UNICO = {
    "id": 2, "nombre": "MATRICULA", "valor": 300_000.0, "tipo_cobro": "unico",
    "activo": True, "mes_inicial": None, "mes_final": 12, "frecuencia_meses": 1,
    "dia_limite_mes": None, "dias_gracia": 0, "mora_tipo": None, "mora_valor": 0.0,
    "anio": 2026,
}


class BaseDeCartera:
    """Lo que cartera lee de la base, sin lo que ya calcula `cobros`.

    Ana (7) esta activa y Luis (9) se retiro: los dos deben la matricula del
    curso 3. Ana tiene una venta pendiente de 20.000. Luis solo sale si la
    consulta **no** filtra a los activos.
    """

    def __init__(self):
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        if sql == SQL_POR_ID:
            self._filas = [ANIOS_DOS[params[0]]] if params[0] in ANIOS_DOS else []
        elif "information_schema.tables" in sql:
            self._filas = [(1,)]
        elif "FROM tipos_pagos_cursos WHERE activo = TRUE" in sql:
            self._filas = [(3, 2, 300_000)]
        elif "JOIN matriculas m ON m.estudiante_id = e.id" in sql:
            ana = (7, "Ana", "Rios", "Activo", 3, "PRIMERO A")
            luis = (9, "Luis", "Mora", "Retirado", 3, "PRIMERO A")
            self._filas = [ana] if "ILIKE 'activo'" in sql else [ana, luis]
        elif "FROM ventas" in sql:
            self._filas = [(7, 50, None, 20_000, 0)]
        else:
            raise AssertionError(f"consulta inesperada: {sql}")

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)

    def close(self):
        pass


@pytest.fixture
def cartera(monkeypatch):
    """La cartera real con la base de arriba; anota el año con que se llama a cobros."""
    from app.controllers import cartera_mora_controller

    base = BaseDeCartera()
    anios = []

    def anotar(resultado):
        def falso(*args, anio_lectivo_id=None, **kwargs):
            anios.append(anio_lectivo_id)
            return resultado
        return falso

    monkeypatch.setattr(cartera_mora_controller, "get_connection", lambda: ConexionFalsa(base))
    monkeypatch.setattr(cartera_mora_controller, "obtener_tipos_pago", anotar([CONCEPTO_UNICO]))
    monkeypatch.setattr(
        cartera_mora_controller, "obtener_valores_personalizados_por_estudiantes",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        cartera_mora_controller, "obtener_pagos_por_concepto_estudiantes", anotar(({}, {}, {}))
    )
    monkeypatch.setattr(
        cartera_mora_controller, "calcular_deudas_anios_anteriores", anotar({})
    )
    return cartera_mora_controller, base, anios


def _resumen_de(items):
    return [(i["estudiante_id"], i["deuda_academica"], i["deuda_inventario"]) for i in items]


def test_la_cartera_del_anio_activo_queda_como_hoy(cartera):
    controlador_cartera, base, anios = cartera

    items = controlador_cartera.reporte_cartera_vencida()

    # Solo activos, con su venta pendiente; todo con el año activo.
    assert _resumen_de(items) == [(7, 300_000, 20_000)]
    assert anios == [None, None, None]
    [estudiantes] = [sql for sql, _ in base.consultas if "JOIN matriculas m" in sql]
    assert SOLO_EL_ACTIVO.replace("c.", "m.") in estudiantes
    assert any("FROM ventas" in sql for sql, _ in base.consultas)


def test_la_cartera_de_2026_muestra_a_quien_se_retiro_debiendo_y_no_las_ventas(cartera):
    """Decisiones 18 y 19: mirando un año que no es el activo salen todos sus
    matriculados que deben, aunque se hayan retirado, y ninguna venta."""
    controlador_cartera, base, anios = cartera

    items = controlador_cartera.reporte_cartera_vencida(anio_lectivo_id=1)

    assert _resumen_de(items) == [(7, 300_000, 0), (9, 300_000, 0)]
    assert anios == [1, 1, 1]
    assert base.consultas[0] == (SQL_POR_ID, (1,))
    assert not any("FROM ventas" in sql for sql, _ in base.consultas)
    [(estudiantes, params)] = [c for c in base.consultas if "JOIN matriculas m" in c[0]]
    assert "m.anio_lectivo_id = %s" in estudiantes
    assert "ILIKE 'activo'" not in estudiantes
    assert params == (1,)


def test_la_cartera_pedida_con_el_id_del_activo_es_la_del_activo(cartera):
    controlador_cartera, base, anios = cartera

    items = controlador_cartera.reporte_cartera_vencida(anio_lectivo_id=2)

    assert _resumen_de(items) == [(7, 300_000, 20_000)]
    assert anios == [2, 2, 2]


def test_la_cartera_por_curso_pone_el_anio_antes_del_curso(cartera):
    controlador_cartera, base, _ = cartera

    controlador_cartera.reporte_cartera_vencida(curso_id=3, anio_lectivo_id=1)

    [(estudiantes, params)] = [c for c in base.consultas if "JOIN matriculas m" in c[0]]
    assert "m.curso_id = %s" in estudiantes
    assert params == (1, 3)


def test_el_resumen_de_cartera_es_del_anio_pedido(cartera):
    controlador_cartera, _, anios = cartera

    resumen = controlador_cartera.resumen_cartera_vencida(anio_lectivo_id=1)

    assert resumen["total_estudiantes"] == 2
    assert resumen["total_inventario"] == 0
    assert anios == [1, 1, 1]


def test_la_cartera_de_un_anio_que_no_existe_no_calcula_nada(cartera):
    controlador_cartera, base, anios = cartera

    with pytest.raises(ValueError, match="El año lectivo seleccionado no existe."):
        controlador_cartera.reporte_cartera_vencida(anio_lectivo_id=99)

    assert base.consultas == [(SQL_POR_ID, (99,))]
    assert anios == []


# ---------------------------------------------------------------------------
# Estado de cuenta por curso: el año de su curso.
# ---------------------------------------------------------------------------


class BaseDeEstadoDeCuenta:
    """El curso 3 es de 2026 (cerrado) y el 30 de 2027 (activo)."""

    ANIO_DEL_CURSO = {3: (1, "cerrado"), 30: (2, "activo")}

    def __init__(self):
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        if "FROM cursos c JOIN anios_lectivos al" in sql:
            self._filas = [self.ANIO_DEL_CURSO[params[0]]]
        elif "WHERE m.curso_id = %s" in sql and "al.estado" in sql:
            anio, estado = self.ANIO_DEL_CURSO[params[0]]
            self._filas = [(7, "Ana", "Rios", anio, estado)]
        elif "WHERE m.curso_id = %s" in sql:
            self._filas = [(7, "Ana", "Rios")]
        elif "FROM pagos" in sql and "STRING_AGG" in sql:
            self._filas = [(50, "Abono")]
        elif "FROM pagos" in sql:
            self._filas = []
        else:
            raise AssertionError(f"consulta inesperada: {sql}")

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)

    def close(self):
        pass


@pytest.fixture
def estado_de_cuenta(monkeypatch):
    from app.controllers import estado_cuenta_controller

    base = BaseDeEstadoDeCuenta()
    llamadas = []

    def calcular(cursor, estudiante_id, **kwargs):
        llamadas.append(kwargs)
        return {"total_deuda": 100}

    monkeypatch.setattr(estado_cuenta_controller, "get_connection", lambda: ConexionFalsa(base))
    monkeypatch.setattr(estado_cuenta_controller, "calcular_deudas_estudiante", calcular)
    return estado_cuenta_controller, base, llamadas


def test_el_estado_de_cuenta_de_un_curso_de_2026_calcula_en_2026(estado_de_cuenta):
    controlador_cuentas, base, llamadas = estado_de_cuenta

    [fila] = controlador_cuentas.estado_cuenta_curso_controller(3)

    assert fila["deuda"] == 100 and fila["pagado"] == 50
    assert llamadas == [{"anio_lectivo_id": 1}]
    [(pagos, params)] = [c for c in base.consultas if "STRING_AGG" in c[0]]
    assert "pagos.anio_lectivo_id = %s" in pagos
    assert params == (7, 1)


def test_el_estado_de_cuenta_de_un_curso_del_anio_activo_es_el_de_siempre(estado_de_cuenta):
    controlador_cuentas, base, llamadas = estado_de_cuenta

    controlador_cuentas.estado_cuenta_curso_controller(30)

    assert llamadas == [{}]
    [(pagos, params)] = [c for c in base.consultas if "STRING_AGG" in c[0]]
    assert _normalizar(f"pagos.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}") in pagos
    assert params == (7,)
    # El año viaja en la consulta de estudiantes: ni una ida mas.
    assert len(base.consultas) == 2


@pytest.fixture
def reporte_de_curso(monkeypatch):
    from app.controllers import reportes_controller

    base = BaseDeEstadoDeCuenta()
    anios = []

    def anotar(resultado):
        def falso(*args, anio_lectivo_id=None, **kwargs):
            anios.append(anio_lectivo_id)
            return resultado
        return falso

    monkeypatch.setattr(reportes_controller, "get_connection", lambda: ConexionFalsa(base))
    monkeypatch.setattr(reportes_controller, "obtener_tipos_pago", anotar([]))
    monkeypatch.setattr(
        reportes_controller, "obtener_asignaciones_cobro_por_curso", lambda *a, **k: {}
    )
    monkeypatch.setattr(
        reportes_controller, "obtener_pagos_por_concepto_estudiantes", anotar(({}, {}, {}))
    )
    monkeypatch.setattr(reportes_controller, "tabla_pagos_aplicaciones_existe", lambda *a: True)
    monkeypatch.setattr(
        reportes_controller, "obtener_valores_personalizados_por_estudiantes", lambda *a, **k: {}
    )
    monkeypatch.setattr(reportes_controller, "construir_estado_cuenta_curso", lambda **k: ["ok"])
    return reportes_controller, base, anios


def test_el_reporte_de_un_curso_de_2026_calcula_en_2026(reporte_de_curso):
    controlador_reportes, base, anios = reporte_de_curso

    assert controlador_reportes.reporte_estado_cuenta_curso_controller(3) == ["ok"]

    assert anios == [1, 1]
    pagos = [c for c in base.consultas if "FROM pagos" in c[0]]
    assert len(pagos) == 3
    assert all("pagos.anio_lectivo_id = %s" in sql for sql, _ in pagos)
    assert all(params == ((7,), 1) for _, params in pagos)


def test_el_reporte_de_un_curso_del_anio_activo_es_el_de_siempre(reporte_de_curso):
    controlador_reportes, base, anios = reporte_de_curso

    controlador_reportes.reporte_estado_cuenta_curso_controller(30)

    assert anios == [None, None]
    pagos = [c for c in base.consultas if "FROM pagos" in c[0]]
    assert all(ANIO_ACTIVO_ID_SQL in sql for sql, _ in pagos)
    assert all(params == ((7,),) for _, params in pagos)


# ---------------------------------------------------------------------------
# Las rutas del paso 3.4, por HTTP.
# ---------------------------------------------------------------------------

RUTAS_CON_ANIO_34 = {
    "/estudiantes": ("routes.estudiantes", "obtener_estudiantes_controller"),
    "/cartera/mora": ("routes.cartera", "reporte_cartera_vencida"),
    "/cartera/mora/resumen": ("routes.cartera", "resumen_cartera_vencida"),
}


@pytest.fixture
def app_admin_34(monkeypatch):
    import importlib

    from app.dependencies import get_current_user
    from app.main import app

    recibido = []

    def doblar(ruta, error=None):
        modulo, nombre = RUTAS_CON_ANIO_34[ruta]

        def falso(*args, **kwargs):
            recibido.append(kwargs.get("anio_lectivo_id"))
            if error is not None:
                raise error
            return []

        monkeypatch.setattr(importlib.import_module(f"app.{modulo}"), nombre, falso)

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app, doblar, recibido
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.parametrize("ruta", sorted(RUTAS_CON_ANIO_34))
def test_las_rutas_del_paso_34_pasan_el_anio(app_admin_34, ruta):
    app, doblar, recibido = app_admin_34
    doblar(ruta)

    assert peticion_get(app, ruta)[0] == 200
    assert peticion_get(app, _con_anio(ruta, 5))[0] == 200
    assert peticion_get(app, _con_anio(ruta, 0))[0] == 422
    assert recibido == [None, 5]


@pytest.mark.parametrize("ruta", sorted(RUTAS_CON_ANIO_34))
def test_las_rutas_del_paso_34_responden_404_si_el_anio_no_existe(app_admin_34, ruta):
    app, doblar, _ = app_admin_34
    doblar(ruta, error=ValueError("El año lectivo seleccionado no existe."))

    status, cuerpo = peticion_get(app, _con_anio(ruta, 99))

    assert status == 404
    assert cuerpo == {"detail": "El año lectivo seleccionado no existe."}


# ===========================================================================
# Paso 3.5a: boletin, reporte parcial y puesto por año.
# ===========================================================================

CURSO_DE_LA_MATRICULA = _normalizar(
    "(SELECT m.curso_id FROM matriculas m"
    " WHERE m.estudiante_id = e.id AND m.anio_lectivo_id = %s)"
)

# funcion del repositorio -> (argumentos, parametros de siempre)
LECTURAS_DEL_CURSO = {
    "leer_materias_del_estudiante": ((8, 2, "ASISTENCIA"), (2, 2, 8, "ASISTENCIA")),
    "leer_datos_del_estudiante": ((8,), (8,)),
    "leer_datos_basicos_del_estudiante": ((8,), (8,)),
    "leer_planilla_vigente": ((8, 2, "ASISTENCIA"), (2, 8, "ASISTENCIA")),
}
CON_FOTO_DE_MATERIAS = {"leer_materias_del_estudiante", "leer_planilla_vigente"}


@pytest.mark.parametrize("nombre", sorted(LECTURAS_DEL_CURSO))
def test_sin_anio_las_lecturas_del_boletin_usan_el_curso_actual_como_siempre(nombre):
    """Comparadas el 2026-10-02 contra el commit anterior: texto y parametros
    identicos. Aqui se fija lo esencial: el curso es `e.curso_id`, sin
    matriculas, y los parametros son los de siempre."""
    from app.repositories import boletin_repository

    argumentos, params = LECTURAS_DEL_CURSO[nombre]
    cursor = CursorQueAnota()

    getattr(boletin_repository, nombre)(cursor, *argumentos)

    [(sql, recibidos)] = cursor.consultas
    assert "e.curso_id" in sql
    assert "matriculas" not in sql
    assert recibidos == params


@pytest.mark.parametrize("nombre", sorted(LECTURAS_DEL_CURSO))
def test_con_anio_las_lecturas_del_boletin_usan_el_curso_de_la_matricula(nombre):
    from app.repositories import boletin_repository

    argumentos, params = LECTURAS_DEL_CURSO[nombre]
    cursor = CursorQueAnota()

    getattr(boletin_repository, nombre)(cursor, *argumentos, anio_lectivo_id=1)

    [(sql, recibidos)] = cursor.consultas
    assert CURSO_DE_LA_MATRICULA in sql
    assert "e.curso_id" not in sql
    # El año va primero: el curso aparece en el FROM, antes que los demas.
    # Desde la fase 6.3b, las dos consultas de materias repiten el año al
    # final para ocultar las de su foto si el año está cerrado.
    extra = (1, 1) if nombre in CON_FOTO_DE_MATERIAS else ()
    assert recibidos == (1, *params, *extra)


class BaseDePuesto:
    """Definitivas del periodo 1 de dos años, contestadas como PostgreSQL.

    2026 es el año 1 (curso 3, asignacion 300); 2027 el 2 y activo (curso 30,
    asignacion 3000). Ana (7) saco 2,0 en 2026 y 4,5 en 2027; Beto (8), 5,0 y
    4,0. Los dos estan hoy en el curso 30.

    Solo separa por año si la consulta trae el filtro de año; si no, mezcla
    las definitivas de los dos, como la consulta de antes.
    """

    CURSO_ACTUAL = {7: 30, 8: 30}
    MATRICULA = {(7, 1): 3, (8, 1): 3, (7, 2): 30, (8, 2): 30}
    ANIO_DEL_CURSO = {3: 1, 30: 2}
    CURSO_DE_ASIGNACION = {300: 3, 3000: 30}
    DEFINITIVAS = [  # (estudiante, asignacion, periodo, definitiva)
        (7, 300, 1, 2.0), (8, 300, 1, 5.0),
        (7, 3000, 1, 4.5), (8, 3000, 1, 4.0),
    ]

    def __init__(self):
        self.consultas = []
        self._fila = None

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        params = list(params)
        if CURSO_DE_LA_MATRICULA in sql:
            anio = params[0]
            curso_de = {e: self.MATRICULA.get((e, anio)) for e in self.CURSO_ACTUAL}
            pedido, anio_filtro, periodo = params[1], params[3], params[4]
        else:
            curso_de = dict(self.CURSO_ACTUAL)
            pedido, periodo = params[0], params[1]
            anio_filtro = 2 if _normalizar(ANIO_ACTIVO_ID_SQL) in sql else None
        if "c.anio_lectivo_id" not in sql:
            anio_filtro = None
        promedios = {}
        for estudiante, asignacion, p, definitiva in self.DEFINITIVAS:
            curso_asignacion = self.CURSO_DE_ASIGNACION[asignacion]
            if p != periodo or curso_de[estudiante] != curso_de[pedido]:
                continue
            if anio_filtro is not None and self.ANIO_DEL_CURSO[curso_asignacion] != anio_filtro:
                continue
            promedios.setdefault(estudiante, []).append(definitiva)
        medias = {e: sum(v) / len(v) for e, v in promedios.items()}
        orden = sorted(medias, key=lambda e: -medias[e])
        puesto = orden.index(params[-1]) + 1 if params[-1] in medias else None
        self._fila = {"puesto": puesto, "total": len(medias)}

    def fetchone(self):
        return self._fila


def test_el_puesto_del_anio_activo_no_mezcla_las_notas_de_2026():
    """El cambio de comportamiento del paso: con 2027 activo, Ana es primera
    en el periodo 1 (4,5 frente a 4,0). Mezclando 2026 seria segunda (3,25
    frente a 4,5)."""
    from app.repositories import boletin_repository

    base = BaseDePuesto()

    fila = boletin_repository.leer_puesto_en_el_curso(base, 7, 1)

    assert fila == {"puesto": 1, "total": 2}
    [(_sql, params)] = base.consultas
    assert params == (7, 1, 7)


def test_el_puesto_de_2026_es_con_las_notas_de_2026():
    from app.repositories import boletin_repository

    base = BaseDePuesto()

    fila = boletin_repository.leer_puesto_en_el_curso(base, 7, 1, anio_lectivo_id=1)

    assert fila == {"puesto": 2, "total": 2}
    [(_sql, params)] = base.consultas
    assert params == (1, 7, 1, 1, 1, 7)


class CursorDeBoletin:
    """Un cursor de diccionarios, como el `RealDictCursor` del boletin."""

    ANIOS = {1: {"id": 1, "anio": 2026, "estado": "cerrado"},
             2: {"id": 2, "anio": 2027, "estado": "activo"}}

    def __init__(self):
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        if sql == SQL_POR_ID:
            self._filas = [self.ANIOS[params[0]]] if params[0] in self.ANIOS else []
        elif "estudiante_nombre" in sql and "curso_nombre" in sql:
            self._filas = [{
                "estudiante_nombre": "Ana", "estudiante_apellido": "Rios",
                "curso_nombre": "PRIMERO A", "jornada": "Mañana",
                "director_grupo_nombre": None, "director_grupo_apellido": None,
            }]
        elif "AS puesto" in sql:
            self._filas = [{"puesto": 1, "total": 2}]
        else:
            self._filas = []

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)

    def close(self):
        pass


class ConexionDeBoletin(ConexionFalsa):
    def cursor(self, *args, **kwargs):
        return self._cursor


def _boletin(monkeypatch, funcion, **kwargs):
    from app.controllers import boletin_controller

    cursor = CursorDeBoletin()
    monkeypatch.setattr(
        boletin_controller, "get_connection", lambda: ConexionDeBoletin(cursor)
    )
    respuesta = getattr(boletin_controller, funcion)(7, 1, **kwargs)
    return respuesta, cursor.consultas


@pytest.mark.parametrize(
    ("funcion", "consultas_de_siempre"),
    [("obtener_boletin_admin_controller", 3), ("obtener_reporte_parcial_admin_controller", 2)],
)
def test_el_boletin_sin_anio_hace_las_consultas_de_siempre(
    monkeypatch, funcion, consultas_de_siempre
):
    """Sin materias, el boletin hace 3 (materias, datos, puesto): la linea base
    de 4 cuenta tambien los detalles, que aqui no hay."""
    _, consultas = _boletin(monkeypatch, funcion)

    assert len(consultas) == consultas_de_siempre
    assert not any("matriculas" in sql for sql, _ in consultas)


@pytest.mark.parametrize(
    "funcion", ["obtener_boletin_admin_controller", "obtener_reporte_parcial_admin_controller"]
)
def test_el_boletin_con_el_id_del_activo_es_el_de_siempre_mas_la_validacion(monkeypatch, funcion):
    _, consultas = _boletin(monkeypatch, funcion, anio_lectivo_id=2)

    assert consultas[0] == (SQL_POR_ID, (2,))
    assert not any("matriculas" in sql for sql, _ in consultas[1:])


@pytest.mark.parametrize(
    "funcion", ["obtener_boletin_admin_controller", "obtener_reporte_parcial_admin_controller"]
)
def test_el_boletin_de_2026_lee_el_curso_de_la_matricula_de_2026(monkeypatch, funcion):
    respuesta, consultas = _boletin(monkeypatch, funcion, anio_lectivo_id=1)

    assert respuesta["curso"] == "PRIMERO A"
    assert consultas[0] == (SQL_POR_ID, (1,))
    for sql, params in consultas[1:]:
        assert CURSO_DE_LA_MATRICULA in sql
        assert params[0] == 1


@pytest.mark.parametrize(
    "funcion", ["obtener_boletin_admin_controller", "obtener_reporte_parcial_admin_controller"]
)
def test_el_boletin_de_un_anio_que_no_existe_no_lee_nada(monkeypatch, funcion):
    from app.services.anio_lectivo import AnioLectivoInexistenteError

    with pytest.raises(AnioLectivoInexistenteError):
        _boletin(monkeypatch, funcion, anio_lectivo_id=99)


RUTAS_DEL_BOLETIN = {
    "/boletines/admin/generar/7/1": "obtener_boletin_admin_controller",
    "/boletines/admin/reporte-parcial/7/1": "obtener_reporte_parcial_admin_controller",
}


@pytest.fixture
def app_admin_boletin(monkeypatch):
    from app.dependencies import get_current_user
    from app.main import app
    from app.routes import boletines

    recibido = []

    def doblar(ruta, error=None):
        def falso(*args, **kwargs):
            recibido.append(kwargs.get("anio_lectivo_id"))
            if error is not None:
                raise error
            return {"estudiante_id": 7}

        monkeypatch.setattr(boletines, RUTAS_DEL_BOLETIN[ruta], falso)

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app, doblar, recibido
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.parametrize("ruta", sorted(RUTAS_DEL_BOLETIN))
def test_las_rutas_del_boletin_pasan_el_anio(app_admin_boletin, ruta):
    app, doblar, recibido = app_admin_boletin
    doblar(ruta)

    assert peticion_get(app, ruta)[0] == 200
    assert peticion_get(app, _con_anio(ruta, 5))[0] == 200
    assert peticion_get(app, _con_anio(ruta, 0))[0] == 422
    assert recibido == [None, 5]


@pytest.mark.parametrize("ruta", sorted(RUTAS_DEL_BOLETIN))
def test_las_rutas_del_boletin_responden_404_si_el_anio_no_existe(app_admin_boletin, ruta):
    from app.services.anio_lectivo import AnioLectivoInexistenteError

    app, doblar, _ = app_admin_boletin
    doblar(ruta, error=AnioLectivoInexistenteError("El año lectivo seleccionado no existe."))

    status, cuerpo = peticion_get(app, _con_anio(ruta, 99))

    assert status == 404
    assert cuerpo == {"detail": "El año lectivo seleccionado no existe."}


@pytest.mark.parametrize("ruta", sorted(RUTAS_DEL_BOLETIN))
def test_otro_valueerror_del_boletin_sigue_siendo_500_sin_su_texto(app_admin_boletin, ruta):
    """Por eso se atrapa el error del año por su nombre: un fallo cualquiera
    no debe salir como 404 ni ensenar su mensaje."""
    app, doblar, _ = app_admin_boletin
    doblar(ruta, error=ValueError("detalle interno"))

    status, cuerpo = peticion_get(app, ruta)

    assert status == 500
    assert "detalle interno" not in cuerpo["detail"]


# ===========================================================================
# Paso 3.5b: observador, detalle del estudiante y planes del admin por año.
# ===========================================================================

ANOTACIONES_DEL_ACTIVO = _normalizar(f"AND a.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}")


class BaseDeBitacora:
    """La bitacora de Ana (55): una anotacion de 2026 (año 1) y una de 2027
    (año 2, activo). Solo deja las de un año si el `ON` trae el filtro."""

    ANOTACIONES = [(901, 1), (902, 2)]  # (id, año)

    def __init__(self):
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        if sql == SQL_POR_ID:
            self._filas = [ANIOS_DOS[params[0]]] if params[0] in ANIOS_DOS else []
            return
        if "FROM estudiantes e JOIN asignaciones a" in sql:  # permiso del profesor
            self._filas = [(1,)]
            return
        if ANOTACIONES_DEL_ACTIVO in sql:
            anio = 2
        elif "AND a.anio_lectivo_id = %s" in sql:
            anio = params[1]
        else:
            anio = None
        self._filas = [
            ("primaria", id_, 7, "Ana", "Ruiz", None, 1, None, None, None, None, None, None, None)
            for id_, anio_anotacion in self.ANOTACIONES
            if anio is None or anio_anotacion == anio
        ]

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)

    def close(self):
        pass


def test_la_bitacora_sin_anio_es_la_del_anio_activo_con_los_parametros_de_siempre():
    base = BaseDeBitacora()

    filas = observador_repository.leer_bitacora(base, 55)
    observador_repository.leer_bitacora(base, 55, 2)

    assert [f[1] for f in filas] == [902]
    (sin_periodo, p1), (con_periodo, p2) = base.consultas
    assert ANOTACIONES_DEL_ACTIVO in sin_periodo
    assert "LEFT JOIN cursos c ON c.id = e.curso_id" in sin_periodo
    assert p1 == (55,) and p2 == (2, 55)
    # Los dos filtros, el del año y el del periodo, van en el ON.
    antes, _, _ = con_periodo.partition("WHERE e.id")
    assert ANOTACIONES_DEL_ACTIVO in antes and "a.periodo = %s" in antes


def test_la_bitacora_de_2026_son_sus_anotaciones_con_el_curso_de_2026():
    base = BaseDeBitacora()

    filas = observador_repository.leer_bitacora(base, 55, None, anio_lectivo_id=1)
    observador_repository.leer_bitacora(base, 55, 3, anio_lectivo_id=1)

    assert [f[1] for f in filas] == [901]
    (sql, p1), (_sql, p2) = base.consultas
    assert CURSO_DE_LA_MATRICULA in sql
    assert p1 == (1, 1, 55) and p2 == (1, 1, 3, 55)


@pytest.fixture
def ruta_del_observador(monkeypatch):
    from app.routes import observador

    base = BaseDeBitacora()

    @contextmanager
    def get_cursor_falso(commit=False, cursor_factory=None):
        yield base

    monkeypatch.setattr(observador, "get_cursor", get_cursor_falso)
    return observador, base


def test_el_admin_lee_la_bitacora_de_2026(ruta_del_observador):
    observador, _ = ruta_del_observador

    respuesta = observador.obtener_observador(55, None, ADMIN, 1)

    assert [a["id"] for a in respuesta["anotaciones"]] == [901]


def test_el_profesor_ve_solo_las_anotaciones_del_anio_activo(ruta_del_observador):
    observador, _ = ruta_del_observador

    respuesta = observador.obtener_observador(55, None, PROFESOR)
    con_el_activo = observador.obtener_observador(55, None, PROFESOR, 2)

    assert [a["id"] for a in respuesta["anotaciones"]] == [902]
    assert [a["id"] for a in con_el_activo["anotaciones"]] == [902]


def test_el_profesor_no_puede_pedir_la_bitacora_de_otro_anio(ruta_del_observador):
    from fastapi import HTTPException

    observador, base = ruta_del_observador

    with pytest.raises(HTTPException) as error:
        observador.obtener_observador(55, None, PROFESOR, 1)

    assert error.value.status_code == 403
    assert error.value.detail == "Solo se puede consultar el año lectivo activo."
    assert not any("observador_anotaciones" in sql for sql, _ in base.consultas)


def test_la_bitacora_de_un_anio_que_no_existe_da_404(ruta_del_observador):
    from fastapi import HTTPException

    observador, _ = ruta_del_observador

    with pytest.raises(HTTPException) as error:
        observador.obtener_observador(55, None, ADMIN, 99)

    assert error.value.status_code == 404
    assert error.value.detail == "El año lectivo seleccionado no existe."


# ---------------------------------------------------------------------------
# Detalle del estudiante.
# ---------------------------------------------------------------------------


class BaseDeExpediente:
    """Las faltas de Ana (55): una en una clase de 2026 (asignacion 300), una
    en 2027 (3000, activo) y una vieja sin clase. Separa por año solo si la
    consulta trae el filtro, y cuenta las sin clase solo si lo pide."""

    FALTAS = [300, 3000, None]
    ANIO_DE_ASIGNACION = {300: 1, 3000: 2}

    def __init__(self):
        self.consultas = []
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        if "FROM asistencia" not in sql:
            self._filas = []
            return
        if SOLO_EL_ACTIVO in sql:
            anio = 2
        elif SOLO_EL_PEDIDO in sql:
            anio = params[1]
        else:
            anio = None
        cuenta_sin_clase = "asignacion_id IS NULL OR" in sql
        total = sum(
            1 for asignacion in self.FALTAS
            if anio is None
            or (asignacion is None and cuenta_sin_clase)
            or (asignacion is not None and self.ANIO_DE_ASIGNACION[asignacion] == anio)
        )
        self._filas = [(total,)]

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)


def test_las_faltas_del_anio_activo_siguen_contando_las_que_no_tienen_clase():
    """Hoy esas filas se cuentan: en el año activo se siguen contando."""
    base = BaseDeExpediente()

    assert estudiantes_repository.contar_inasistencias(base, 55) == 2
    [(_sql, params)] = base.consultas
    assert params == (55,)


def test_las_faltas_de_2026_son_solo_las_de_sus_clases():
    base = BaseDeExpediente()

    assert estudiantes_repository.contar_inasistencias(base, 55, anio_lectivo_id=1) == 1
    [(sql, params)] = base.consultas
    assert "asignacion_id IS NULL" not in sql
    assert params == (55, 1)


@pytest.mark.parametrize("leer", ["leer_promedios_por_materia", "leer_observaciones"])
def test_notas_y_observaciones_del_expediente_son_del_anio(leer):
    cursor = CursorQueAnota()

    getattr(estudiantes_repository, leer)(cursor, 55)
    getattr(estudiantes_repository, leer)(cursor, 55, anio_lectivo_id=1)

    (activo, p1), (otro, p2) = cursor.consultas
    assert SOLO_EL_ACTIVO in activo and p1 == (55,)
    assert SOLO_EL_PEDIDO in otro and p2 == (55, 1)


@pytest.fixture
def expediente(monkeypatch):
    base = BaseDeBitacora()  # solo responde a la validacion del año
    llamadas = []

    def calcular(cursor, estudiante_id, **kwargs):
        llamadas.append(kwargs)
        return {"deudas": [], "curso_id": 3}

    monkeypatch.setattr(estudiante_controller, "get_connection", lambda: ConexionFalsa(base))
    monkeypatch.setattr(estudiante_controller, "calcular_deudas_estudiante", calcular)
    for nombre in (
        "leer_promedios_por_materia", "contar_inasistencias",
        "leer_observaciones", "leer_cargos_de_inventario",
    ):
        def falso(cursor, est_id, anio_lectivo_id="no-se-paso", _nombre=nombre):
            llamadas.append((_nombre, anio_lectivo_id))
            return 0 if _nombre == "contar_inasistencias" else []
        monkeypatch.setattr(estudiante_controller.estudiantes_repository, nombre, falso)
    return llamadas


def test_el_expediente_de_2026_pide_todo_en_2026_menos_el_inventario(expediente):
    estudiante_controller.obtener_detalles_estudiante_controller(55, anio_lectivo_id=1)

    assert expediente == [
        ("leer_promedios_por_materia", 1),
        ("contar_inasistencias", 1),
        ("leer_observaciones", 1),
        {"anio_lectivo_id": 1},
        ("leer_cargos_de_inventario", "no-se-paso"),
    ]


def test_el_expediente_con_el_activo_es_el_de_siempre(expediente):
    estudiante_controller.obtener_detalles_estudiante_controller(55, anio_lectivo_id=2)

    assert expediente == [
        ("leer_promedios_por_materia", None),
        ("contar_inasistencias", None),
        ("leer_observaciones", None),
        {},
        ("leer_cargos_de_inventario", "no-se-paso"),
    ]


def test_el_expediente_de_un_anio_que_no_existe_no_se_disfraza_de_seccion_rota(expediente):
    """Un año invalido no es una seccion que falla: la peticion entera se rechaza."""
    from app.services.anio_lectivo import AnioLectivoInexistenteError

    with pytest.raises(AnioLectivoInexistenteError):
        estudiante_controller.obtener_detalles_estudiante_controller(55, anio_lectivo_id=99)

    assert expediente == []


# ---------------------------------------------------------------------------
# Planes de clase del admin.
# ---------------------------------------------------------------------------


def _planes(monkeypatch, **filtros):
    from app.repositories import plan_de_clases_repository

    cursor = CursorQueAnota(una=[(0,)])

    @contextmanager
    def get_cursor_falso(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", get_cursor_falso)
    plan_de_clases_repository.listar_planes_admin(profesor_id=7, **filtros)
    return cursor.consultas


def test_los_planes_del_admin_sin_anio_son_del_activo_con_los_parametros_de_siempre(monkeypatch):
    (conteo, p1), (pagina, p2) = _planes(monkeypatch)

    assert SOLO_EL_ACTIVO in conteo and SOLO_EL_ACTIVO in pagina
    assert p1 == (7,) and p2 == (7, 50, 0)


def test_los_planes_del_admin_de_otro_anio(monkeypatch):
    (conteo, p1), (pagina, p2) = _planes(monkeypatch, anio_lectivo_id=1)

    assert SOLO_EL_PEDIDO in conteo and SOLO_EL_PEDIDO in pagina
    assert p1 == (7, 1) and p2 == (7, 1, 50, 0)


# ---------------------------------------------------------------------------
# Las rutas del 3.5b, por HTTP.
# ---------------------------------------------------------------------------

RUTAS_DEL_35B = {
    "/estudiantes/55/detalles": ("routes.estudiantes", "obtener_detalles_estudiante_controller"),
    "/admin/plan-de-clases": ("routes.plan_de_clases", "listar_planes_admin_controller"),
}


@pytest.mark.parametrize("ruta", sorted(RUTAS_DEL_35B))
def test_las_rutas_del_35b_pasan_el_anio(monkeypatch, ruta):
    import importlib

    from app.dependencies import get_current_user
    from app.main import app

    modulo, nombre = RUTAS_DEL_35B[ruta]
    recibido = []

    def falso(*args, **kwargs):
        recibido.append(kwargs.get("anio_lectivo_id"))
        return {}

    monkeypatch.setattr(importlib.import_module(f"app.{modulo}"), nombre, falso)
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        assert peticion_get(app, ruta)[0] == 200
        assert peticion_get(app, _con_anio(ruta, 5))[0] == 200
        assert peticion_get(app, _con_anio(ruta, 0))[0] == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert recibido == [None, 5]


def test_el_detalle_de_un_anio_que_no_existe_responde_404(monkeypatch):
    from app.dependencies import get_current_user
    from app.main import app
    from app.routes import estudiantes
    from app.services.anio_lectivo import AnioLectivoInexistenteError

    def falso(*args, **kwargs):
        raise AnioLectivoInexistenteError("El año lectivo seleccionado no existe.")

    monkeypatch.setattr(estudiantes, "obtener_detalles_estudiante_controller", falso)
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        status, cuerpo = peticion_get(app, "/estudiantes/55/detalles?anio_lectivo_id=99")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert status == 404
    assert cuerpo == {"detail": "El año lectivo seleccionado no existe."}
