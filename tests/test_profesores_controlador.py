"""Caracterizacion de obtener_clases_profesor_controller, migrada en 1.4f.

Es la unica funcion desprotegida que quedaba en profesor_controller.

Ojo con el nombre: existe otra funcion homonima en asignacion_controller que
consulta lo mismo pero SI filtra por asignacion activa y por estado del curso y
la materia. Esta no filtra nada. La diferencia es previa a la migracion y se
conserva tal cual; la prueba la deja explicita para que nadie la confunda.
"""

from contextlib import contextmanager

import pytest

from app.controllers import profesor_controller


class CursorFalso:
    def __init__(self, filas):
        self.filas = list(filas)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchall(self):
        return self.filas


@pytest.fixture
def cursor_de(monkeypatch):
    def instalar(filas=()):
        cursor = CursorFalso(filas)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        monkeypatch.setattr(profesor_controller, "get_cursor", fake_get_cursor)
        return cursor, commits

    return instalar


def test_clases_profesor_devuelve_asignacion_curso_y_materia(cursor_de):
    cursor, commits = cursor_de(filas=[(12, "Quinto A", "Matemáticas")])

    resultado = profesor_controller.obtener_clases_profesor_controller(9)

    query, params = cursor.calls[0]
    assert "FROM asignaciones a" in query
    assert "JOIN cursos c ON c.id = a.curso_id" in query
    assert "JOIN materias m ON m.id = a.materia_id" in query
    assert params == (9,)
    assert commits == [False]
    assert resultado == [
        {"asignacion_id": 12, "curso": "Quinto A", "materia": "Matemáticas"}
    ]


def test_clases_profesor_no_filtra_por_asignacion_activa(cursor_de):
    cursor, _ = cursor_de(filas=[])

    profesor_controller.obtener_clases_profesor_controller(9)

    query, _ = cursor.calls[0]
    assert "activo" not in query
    assert "estado" not in query


def test_clases_profesor_sin_asignaciones_devuelve_lista_vacia(cursor_de):
    cursor_de(filas=[])

    assert profesor_controller.obtener_clases_profesor_controller(9) == []
