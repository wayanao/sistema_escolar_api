"""Fase 5.3: crear el año siguiente y dar altas manuales en preparación.

Las pruebas usan dobles de base de datos: no crean 2027 ni se conectan a un
tenant real. También fijan que omitir ``anio_lectivo_id`` conserva el camino
anterior de cursos y conceptos de pago.
"""
import asyncio
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import anios_lectivos_controller, curso_controller
from app.controllers import tipos_pagos_controller
from app.repositories import anios_lectivos_repository
from app.routes import anios_lectivos as rutas_anios
from app.routes import cursos as rutas_cursos
from app.routes import tipos_pagos as rutas_tipos_pagos
from app.services.anio_lectivo import AnioLectivoNoEditableError


ADMIN = {"id": 1, "rol": "admin"}
PROFESOR = {"id": 7, "rol": "profesor"}


class CursorFalso:
    def __init__(self, respuestas=()):
        self.respuestas = list(respuestas)
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.respuestas.pop(0) if self.respuestas else None

    def close(self):
        pass


class ConexionFalsa:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def _curso(anio_lectivo_id=None):
    return SimpleNamespace(
        nombre="Primero A",
        jornada="Mañana",
        estado="activo",
        nivel="primaria",
        director_grupo_id=None,
        anio_lectivo_id=anio_lectivo_id,
    )


def _peticion(app, metodo, ruta, cuerpo=None):
    crudo = json.dumps(cuerpo).encode() if cuerpo is not None else b""
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

    asyncio.run(app(scope, receive, send))
    return salida["status"], json.loads(salida["body"].decode())


# ---------------------------------------------------------------------------
# Crear exactamente N+1 en preparación.
# ---------------------------------------------------------------------------


def test_el_repositorio_bloquea_el_activo_antes_de_preparar_el_siguiente():
    cursor = CursorFalso([(2, 2026, "activo")])

    fila = anios_lectivos_repository.leer_anio_activo_para_actualizar(cursor)

    assert fila == (2, 2026, "activo")
    sql, params = cursor.consultas[0]
    assert sql.endswith("WHERE estado = 'activo' FOR UPDATE")
    assert params is None


def test_el_repositorio_crea_un_anio_en_preparacion_sin_activarlo():
    cursor = CursorFalso([(3, 2027, "preparacion")])

    fila = anios_lectivos_repository.crear_anio_en_preparacion(cursor, 2027)

    assert fila == (3, 2027, "preparacion")
    sql, params = cursor.consultas[0]
    assert "INSERT INTO anios_lectivos (anio, estado)" in sql
    assert "VALUES (%s, 'preparacion')" in sql
    assert "ON CONFLICT DO NOTHING" in sql
    assert "RETURNING id, anio, estado" in sql
    assert params == (2027,)


@pytest.fixture
def entorno_crear_anio(monkeypatch):
    estado = SimpleNamespace(
        activo=(2, 2026, "activo"),
        preparacion=None,
        creada=(3, 2027, "preparacion"),
        eventos=[],
    )
    cursor = object()

    @contextmanager
    def get_cursor_falso(commit=False):
        estado.eventos.append(("abre", commit))
        yield cursor
        estado.eventos.append(("cierra",))

    def leer_activo(cursor_recibido):
        estado.eventos.append(("activo", cursor_recibido is cursor))
        return estado.activo

    def leer_preparacion(cursor_recibido):
        estado.eventos.append(("preparacion", cursor_recibido is cursor))
        return estado.preparacion

    def crear(cursor_recibido, anio):
        estado.eventos.append(("crear", cursor_recibido is cursor, anio))
        return estado.creada

    monkeypatch.setattr(anios_lectivos_controller, "get_cursor", get_cursor_falso)
    monkeypatch.setattr(
        anios_lectivos_controller.anios_lectivos_repository,
        "leer_anio_activo_para_actualizar",
        leer_activo,
    )
    monkeypatch.setattr(
        anios_lectivos_controller.anios_lectivos_repository,
        "leer_anio_en_preparacion",
        leer_preparacion,
    )
    monkeypatch.setattr(
        anios_lectivos_controller.anios_lectivos_repository,
        "crear_anio_en_preparacion",
        crear,
    )
    return estado


def test_crear_anio_toma_el_activo_y_crea_exactamente_el_siguiente(entorno_crear_anio):
    resultado = anios_lectivos_controller.crear_anio_lectivo_controller()

    assert resultado == {"id": 3, "anio": 2027, "estado": "preparacion"}
    assert entorno_crear_anio.eventos == [
        ("abre", True),
        ("activo", True),
        ("preparacion", True),
        ("crear", True, 2027),
        ("cierra",),
    ]


def test_no_crea_otro_anio_si_ya_hay_uno_en_preparacion(entorno_crear_anio):
    entorno_crear_anio.preparacion = (3, 2027, "preparacion")

    with pytest.raises(anios_lectivos_controller.AnioLectivoEnPreparacionError):
        anios_lectivos_controller.crear_anio_lectivo_controller()

    assert not any(evento[0] == "crear" for evento in entorno_crear_anio.eventos)


def test_no_inventa_el_siguiente_si_no_hay_anio_activo(entorno_crear_anio):
    entorno_crear_anio.activo = None

    with pytest.raises(anios_lectivos_controller.AnioLectivoActivoInexistenteError):
        anios_lectivos_controller.crear_anio_lectivo_controller()

    assert not any(evento[0] == "crear" for evento in entorno_crear_anio.eventos)


def test_un_choque_al_crear_el_siguiente_se_informa_como_conflicto(
    entorno_crear_anio,
):
    entorno_crear_anio.creada = None

    with pytest.raises(anios_lectivos_controller.AnioLectivoSiguienteExistenteError):
        anios_lectivos_controller.crear_anio_lectivo_controller()


def test_la_ruta_de_creacion_es_solo_para_admin(monkeypatch):
    from app.dependencies import get_current_user
    from app.main import app

    monkeypatch.setattr(
        rutas_anios,
        "crear_anio_lectivo_controller",
        lambda: {"id": 3, "anio": 2027, "estado": "preparacion"},
    )
    app.dependency_overrides[get_current_user] = lambda: PROFESOR
    try:
        status, cuerpo = _peticion(app, "POST", "/anios-lectivos")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert status == 403
    assert cuerpo == {"detail": "No tienes los permisos necesarios"}


def test_el_admin_crea_el_anio_sin_enviar_el_numero(monkeypatch):
    from app.dependencies import get_current_user
    from app.main import app

    monkeypatch.setattr(
        rutas_anios,
        "crear_anio_lectivo_controller",
        lambda: {"id": 3, "anio": 2027, "estado": "preparacion"},
    )
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        status, cuerpo = _peticion(app, "POST", "/anios-lectivos")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert status == 201
    assert cuerpo == {"id": 3, "anio": 2027, "estado": "preparacion"}


# ---------------------------------------------------------------------------
# Altas manuales: el año es opcional y el servidor lo valida.
# ---------------------------------------------------------------------------


def test_crear_curso_en_preparacion_valida_y_escribe_el_anio(monkeypatch):
    cursor = CursorFalso([(3, 2027, "preparacion"), None, (21,)])
    conexion = ConexionFalsa(cursor)
    monkeypatch.setattr(curso_controller, "get_connection", lambda: conexion)

    curso_id = curso_controller.crear_curso_controller(_curso(anio_lectivo_id=3))

    assert curso_id == 21
    assert cursor.consultas[0][1] == (3,)
    sql_duplicado, params_duplicado = cursor.consultas[1]
    assert "anio_lectivo_id = %s" in sql_duplicado
    assert params_duplicado == ("PRIMERO A", "Mañana", None, None, 3)
    sql_insert, params_insert = cursor.consultas[2]
    assert "VALUES (%s, %s, %s, %s, %s, %s)" in sql_insert
    assert params_insert == ("PRIMERO A", "Mañana", "activo", "primaria", None, 3)
    assert conexion.commits == 1


@pytest.mark.parametrize("estado", ["cerrado", "desconocido"])
def test_crear_curso_rechaza_un_anio_no_editable(monkeypatch, estado):
    cursor = CursorFalso([(3, 2025, estado)])
    conexion = ConexionFalsa(cursor)
    monkeypatch.setattr(curso_controller, "get_connection", lambda: conexion)

    with pytest.raises(AnioLectivoNoEditableError):
        curso_controller.crear_curso_controller(_curso(anio_lectivo_id=3))

    assert not any("INSERT INTO cursos" in sql for sql, _ in cursor.consultas)
    assert conexion.rollbacks == 1


def test_crear_concepto_en_preparacion_valida_y_escribe_el_anio(monkeypatch):
    cursor = CursorFalso([(3, 2027, "preparacion"), None, (8,)])
    conexion = ConexionFalsa(cursor)
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)

    respuesta = tipos_pagos_controller.crear_tipo_pago(
        "MATRICULA", 300000, anio_lectivo_id=3
    )

    assert respuesta == {"id": 8, "nombre": "MATRICULA", "valor": 300000}
    assert cursor.consultas[0][1] == (3,)
    sql_duplicado, params_duplicado = cursor.consultas[1]
    assert "anio_lectivo_id = %s" in sql_duplicado
    assert params_duplicado == ("MATRICULA", 3)
    sql_insert, params_insert = cursor.consultas[2]
    assert "VALUES (%s, %s, %s)" in sql_insert
    assert params_insert == ("MATRICULA", 300000, 3)
    assert conexion.commits == 1


def test_crear_concepto_rechaza_un_anio_cerrado_sin_ocultar_el_error(monkeypatch):
    cursor = CursorFalso([(3, 2025, "cerrado")])
    conexion = ConexionFalsa(cursor)
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)

    with pytest.raises(AnioLectivoNoEditableError):
        tipos_pagos_controller.crear_tipo_pago("MATRICULA", 300000, anio_lectivo_id=3)

    assert not any("INSERT INTO tipos_de_pagos" in sql for sql, _ in cursor.consultas)
    assert conexion.rollbacks == 1


def test_los_esquemas_de_alta_aceptan_anio_sin_cambiar_los_de_edicion():
    curso_alta = rutas_cursos.CursoCreateConAnio(
        nombre="Primero A", anio_lectivo_id=3
    )
    concepto_alta = rutas_tipos_pagos.TipoPagoCrear(
        nombre="MATRICULA", anio_lectivo_id=3
    )

    assert curso_alta.anio_lectivo_id == 3
    assert concepto_alta.anio_lectivo_id == 3
    assert "anio_lectivo_id" not in rutas_cursos.CursoCreate.model_fields
    assert "anio_lectivo_id" not in rutas_tipos_pagos.TipoPago.model_fields


def test_la_ruta_de_cursos_entrega_el_anio_solo_al_modelo_de_alta(monkeypatch):
    recibidos = []

    def crear_falso(curso):
        recibidos.append(curso.anio_lectivo_id)
        return 21

    monkeypatch.setattr(rutas_cursos, "crear_curso_controller", crear_falso)

    respuesta = rutas_cursos.crear_curso(
        rutas_cursos.CursoCreateConAnio(nombre="Primero A", anio_lectivo_id=3)
    )

    assert respuesta == {"mensaje": "Curso creado", "id": 21}
    assert recibidos == [3]


def test_la_ruta_de_conceptos_entrega_el_anio_si_se_envia(monkeypatch):
    recibidos = []

    def crear_falso(nombre, valor, *, anio_lectivo_id):
        recibidos.append((nombre, valor, anio_lectivo_id))
        return {"id": 8, "nombre": nombre, "valor": valor}

    monkeypatch.setattr(rutas_tipos_pagos, "crear_tipo_pago", crear_falso)

    respuesta = rutas_tipos_pagos.create_tipo_pago(
        rutas_tipos_pagos.TipoPagoCrear(
            nombre="MATRICULA", valor=300000, anio_lectivo_id=3
        )
    )

    assert respuesta == {"id": 8, "nombre": "MATRICULA", "valor": 300000}
    assert recibidos == [("MATRICULA", 300000, 3)]


def test_la_ruta_de_conceptos_no_agrega_argumentos_si_se_omite_el_anio(monkeypatch):
    recibidos = []

    def crear_falso(nombre, valor):
        recibidos.append((nombre, valor))
        return {"id": 8, "nombre": nombre, "valor": valor}

    monkeypatch.setattr(rutas_tipos_pagos, "crear_tipo_pago", crear_falso)

    respuesta = rutas_tipos_pagos.create_tipo_pago(
        rutas_tipos_pagos.TipoPagoCrear(nombre="PENSION", valor=200000)
    )

    assert respuesta == {"id": 8, "nombre": "PENSION", "valor": 200000}
    assert recibidos == [("PENSION", 200000)]
