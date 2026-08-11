"""Caracterizacion del controlador de asignaciones migrado en la subcapa 1.4b.

Cubre las seis funciones que pasaron de get_connection a get_cursor. Fijan
sentencia, parametros, semantica de commit y estructura de la respuesta.

El caso que mas importa es eliminar_asignacion_controller, que tiene dos caminos:
cuando encuentra la asignacion ejecuta SELECT y UPDATE, y cuando no la encuentra
sale por un return temprano tras el SELECT. Antes de migrar, ese segundo camino
perdia la conexion sin cerrarla.
"""

from contextlib import contextmanager

import pytest

from app.controllers import asignacion_controller


class CursorFalso:
    def __init__(self, fila=None, filas=None):
        self.fila = fila
        self.filas = filas or []
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila

    def fetchall(self):
        return self.filas


@pytest.fixture
def cursor_de(monkeypatch):
    def instalar(fila=None, filas=None):
        cursor = CursorFalso(fila=fila, filas=filas)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        monkeypatch.setattr(asignacion_controller, "get_cursor", fake_get_cursor)
        return cursor, commits

    return instalar


def test_cursos_por_profesor_lista_cursos_activos(cursor_de):
    cursor, commits = cursor_de(filas=[(4, "Quinto A"), (5, "Sexto B")])

    resultado = asignacion_controller.cursos_por_profesor_controller(9)

    query, params = cursor.calls[0]
    assert "FROM asignaciones a" in query
    assert "a.activo = TRUE" in query
    assert params == (9,)
    assert commits == [False]
    assert resultado == [
        {"curso_id": 4, "nombre": "Quinto A"},
        {"curso_id": 5, "nombre": "Sexto B"},
    ]


def test_profesor_por_curso_lista_profesores_activos(cursor_de):
    cursor, commits = cursor_de(filas=[(2, "Ana", "Ríos")])

    resultado = asignacion_controller.profesor_por_curso_controller(4)

    query, params = cursor.calls[0]
    assert "JOIN profesor p ON a.profesor_id = p.id" in query
    assert params == (4,)
    assert commits == [False]
    assert resultado == [{"profesor_id": 2, "nombre": "Ana", "apellido": "Ríos"}]


def test_horarios_admin_ordena_por_dia_y_hora(cursor_de):
    fila = ("Ana Ríos", "Quinto A", "Matemáticas", "Lunes", "07:00", "08:00")
    cursor, commits = cursor_de(filas=[fila])

    resultado = asignacion_controller.obtener_horarios_admin_controller()

    query, params = cursor.calls[0]
    assert "WHEN 'Lunes' THEN 1" in query
    assert "a.hora_inicio" in query
    assert params is None
    assert commits == [False]
    assert resultado == [{
        "profesor": "Ana Ríos",
        "curso": "Quinto A",
        "materia": "Matemáticas",
        "dia": "Lunes",
        "hora_inicio": "07:00",
        "hora_fin": "08:00",
    }]


def test_eliminar_asignacion_desactiva_sin_borrar_historial(cursor_de):
    cursor, commits = cursor_de(fila=(88,))

    resultado = asignacion_controller.eliminar_asignacion_controller(9, 4)

    consulta, params_consulta = cursor.calls[0]
    actualizacion, params_actualizacion = cursor.calls[1]
    assert "SELECT id FROM asignaciones" in consulta
    assert params_consulta == (9, 4)
    assert "UPDATE asignaciones" in actualizacion
    assert "SET activo = FALSE" in actualizacion
    assert params_actualizacion == (88,)
    assert commits == [True]
    assert resultado == {
        "mensaje": "Asignación desactivada. El historial académico se conserva."
    }


def test_eliminar_asignacion_inexistente_no_actualiza_nada(cursor_de):
    cursor, commits = cursor_de(fila=None)

    resultado = asignacion_controller.eliminar_asignacion_controller(9, 4)

    assert len(cursor.calls) == 1
    consulta, _ = cursor.calls[0]
    assert "SELECT id FROM asignaciones" in consulta
    assert resultado == {"mensaje": "Asignación no encontrada"}
    # El bloque se abre pidiendo commit y el return temprano lo deja confirmar una
    # transaccion de solo lectura. Es inocuo y sustituye a la fuga anterior, que
    # abandonaba la conexion con la transaccion abierta.
    assert commits == [True]


def test_clases_profesor_devuelve_curso_y_materia(cursor_de):
    cursor, commits = cursor_de(filas=[(12, "Quinto A", "Matemáticas")])

    resultado = asignacion_controller.obtener_clases_profesor_controller(9)

    query, params = cursor.calls[0]
    assert "FROM asignaciones a" in query
    assert params == (9,)
    assert commits == [False]
    assert resultado == [{"id": 12, "curso": "Quinto A", "materia": "Matemáticas"}]


def test_todas_asignaciones_normaliza_horario_ausente(cursor_de):
    fila = (7, 9, 4, 3, None, None, None, "Ana Ríos", "Quinto A", "Matemáticas", 7, 100)
    cursor, commits = cursor_de(filas=[fila])

    resultado = asignacion_controller.obtener_todas_asignaciones_controller()

    query, _ = cursor.calls[0]
    assert "ORDER BY a.id DESC" in query
    assert commits == [False]
    assert resultado == [{
        "id": 7,
        "profesor_id": 9,
        "curso_id": 4,
        "materia_id": 3,
        "dia": "",
        "hora_inicio": "",
        "hora_fin": "",
        "profesor_nombre": "Ana Ríos",
        "curso_nombre": "Quinto A",
        "materia_nombre": "Matemáticas",
        "asignacion_academica_id": 7,
        "orden_boletin": 100,
    }]
