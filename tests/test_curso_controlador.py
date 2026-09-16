"""Caracterizacion de `curso_controller`, con foco en el campo `nivel`
(funcionalidad de nivel academico: preescolar/primaria).

No existia cobertura previa de este controlador; estas pruebas fijan tanto
el comportamiento nuevo (nivel) como el ya existente (nombre, jornada,
estado) que queda expuesto al escribir estas pruebas.
"""
from types import SimpleNamespace

import pytest

from app.controllers import curso_controller


class CursorFalso:
    def __init__(self, fila=None, filas=(), secuencia_fetchone=None):
        self.fila = fila
        self.filas = list(filas)
        self.secuencia_fetchone = list(secuencia_fetchone or [])
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        if self.secuencia_fetchone:
            return self.secuencia_fetchone.pop(0)
        return self.fila

    def fetchall(self):
        return self.filas

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


@pytest.fixture
def cursor_curso(monkeypatch):
    def instalar(fila=None, filas=(), secuencia_fetchone=None):
        cursor = CursorFalso(fila=fila, filas=filas, secuencia_fetchone=secuencia_fetchone)
        conn = ConexionFalsa(cursor)
        monkeypatch.setattr(curso_controller, "get_connection", lambda: conn)
        return cursor, conn

    return instalar


def _datos(
    nombre="Transición A",
    jornada="Mañana",
    estado="activo",
    nivel="preescolar",
    director_grupo_id=None,
):
    return SimpleNamespace(
        nombre=nombre,
        jornada=jornada,
        estado=estado,
        nivel=nivel,
        director_grupo_id=director_grupo_id,
    )


# ---------------------------------------------------------------------------
# Creacion
# ---------------------------------------------------------------------------

def test_crear_curso_guarda_el_nivel(cursor_curso):
    # 1a fetchone: validacion de duplicado (None = no hay). 2a: el RETURNING id.
    cursor, conn = cursor_curso(secuencia_fetchone=[None, (1,)])

    curso_id = curso_controller.crear_curso_controller(_datos(nivel="preescolar"))

    query, params = cursor.calls[-1]
    assert "INSERT INTO cursos" in query
    assert "nivel" in query
    assert params == ("TRANSICIÓN A", "Mañana", "activo", "preescolar", None)
    assert curso_id == 1
    assert conn.commits == 1


def test_crear_curso_sin_nivel_guarda_null(cursor_curso):
    cursor, _ = cursor_curso(secuencia_fetchone=[None, (2,)])

    curso_controller.crear_curso_controller(_datos(nombre="Primero A", nivel=None))

    _, params = cursor.calls[-1]
    assert params[-2] is None  # nivel es el penultimo parametro, antes de director_grupo_id


def test_crear_curso_guarda_el_director_grupo_id(cursor_curso):
    cursor, conn = cursor_curso(secuencia_fetchone=[None, (3,)])

    curso_controller.crear_curso_controller(_datos(director_grupo_id=7))

    query, params = cursor.calls[-1]
    assert "director_grupo_id" in query
    assert params[-1] == 7
    assert conn.commits == 1


def test_crear_curso_sin_director_grupo_guarda_null(cursor_curso):
    cursor, _ = cursor_curso(secuencia_fetchone=[None, (4,)])

    curso_controller.crear_curso_controller(_datos(director_grupo_id=None))

    _, params = cursor.calls[-1]
    assert params[-1] is None


# ---------------------------------------------------------------------------
# Actualizacion
# ---------------------------------------------------------------------------

def test_actualizar_curso_guarda_el_nivel(cursor_curso):
    cursor, conn = cursor_curso(secuencia_fetchone=[None, (5,)])

    resultado = curso_controller.actualizar_curso_controller(5, _datos(nivel="preescolar"))

    query, params = cursor.calls[-1]
    assert "UPDATE cursos" in query
    assert "nivel = %s" in query
    assert params == ("TRANSICIÓN A", "Mañana", "activo", "preescolar", None, 5)
    assert conn.commits == 1
    assert resultado == {"mensaje": "Curso actualizado correctamente"}


def test_actualizar_curso_a_sin_nivel_guarda_null(cursor_curso):
    cursor, _ = cursor_curso(secuencia_fetchone=[None, (5,)])

    curso_controller.actualizar_curso_controller(5, _datos(nivel=None))

    _, params = cursor.calls[-1]
    assert params[-3] is None  # nivel: tercero desde el final, antes de director_grupo_id y curso_id


def test_actualizar_curso_guarda_el_director_grupo_id(cursor_curso):
    cursor, conn = cursor_curso(secuencia_fetchone=[None, (5,)])

    curso_controller.actualizar_curso_controller(5, _datos(director_grupo_id=9))

    query, params = cursor.calls[-1]
    assert "director_grupo_id = %s" in query
    assert params[-2] == 9  # director_grupo_id es el penultimo parametro, antes de curso_id
    assert conn.commits == 1


def test_actualizar_curso_a_sin_director_grupo_guarda_null(cursor_curso):
    cursor, _ = cursor_curso(secuencia_fetchone=[None, (5,)])

    curso_controller.actualizar_curso_controller(5, _datos(director_grupo_id=None))

    _, params = cursor.calls[-1]
    assert params[-2] is None


def test_actualizar_curso_inexistente_no_confirma(cursor_curso):
    # 1a fetchone: sin duplicado. 2a: el UPDATE no encuentra el id.
    cursor, conn = cursor_curso(secuencia_fetchone=[None, None])

    resultado = curso_controller.actualizar_curso_controller(999, _datos())

    assert resultado == {"error": "Curso no encontrado"}
    assert conn.commits == 0
    assert conn.rollbacks == 1


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------

def test_listar_cursos_devuelve_el_nivel_de_cada_uno(cursor_curso):
    cursor, _ = cursor_curso(
        filas=[
            (1, "Transición A", "Mañana", "activo", "preescolar", 7),
            (2, "Primero A", "Mañana", "activo", None, None),
        ]
    )

    resultado = curso_controller.obtener_cursos_controller()

    assert resultado[0]["nivel"] == "preescolar"
    assert resultado[1]["nivel"] is None
    query, _ = cursor.calls[0]
    assert "nivel" in query


def test_listar_cursos_devuelve_el_director_grupo_id_de_cada_uno(cursor_curso):
    cursor, _ = cursor_curso(
        filas=[
            (1, "Transición A", "Mañana", "activo", "preescolar", 7),
            (2, "Primero A", "Mañana", "activo", None, None),
        ]
    )

    resultado = curso_controller.obtener_cursos_controller()

    assert resultado[0]["director_grupo_id"] == 7
    assert resultado[1]["director_grupo_id"] is None
    query, _ = cursor.calls[0]
    assert "director_grupo_id" in query


def test_listar_cursos_paginado_devuelve_el_nivel(cursor_curso):
    cursor, _ = cursor_curso(
        secuencia_fetchone=[(1,)],
        filas=[(1, "Transición A", "Mañana", "activo", "preescolar", 7)],
    )

    resultado = curso_controller.obtener_cursos_paginado_controller()

    assert resultado["items"][0]["nivel"] == "preescolar"
    query_listado, _ = cursor.calls[1]
    assert "nivel" in query_listado


def test_listar_cursos_paginado_devuelve_el_director_grupo_id(cursor_curso):
    cursor, _ = cursor_curso(
        secuencia_fetchone=[(1,)],
        filas=[(1, "Transición A", "Mañana", "activo", "preescolar", 7)],
    )

    resultado = curso_controller.obtener_cursos_paginado_controller()

    assert resultado["items"][0]["director_grupo_id"] == 7
    query_listado, _ = cursor.calls[1]
    assert "director_grupo_id" in query_listado


def test_cambiar_estado_devuelve_el_curso_con_su_nivel(cursor_curso):
    cursor, conn = cursor_curso(
        fila=(1, "Transición A", "Mañana", "inactivo", "preescolar", 7)
    )

    resultado = curso_controller.actualizar_estado_curso_controller(1, "inactivo")

    assert resultado["nivel"] == "preescolar"
    assert resultado["estado"] == "inactivo"
    assert conn.commits == 1


def test_cambiar_estado_devuelve_el_curso_con_su_director_grupo_id(cursor_curso):
    cursor, conn = cursor_curso(
        fila=(1, "Transición A", "Mañana", "inactivo", "preescolar", 7)
    )

    resultado = curso_controller.actualizar_estado_curso_controller(1, "inactivo")

    assert resultado["director_grupo_id"] == 7
    assert conn.commits == 1
