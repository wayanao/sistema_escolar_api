"""Caracterizacion de `resolver_nivel_curso_cursor`.

Fija el SQL exacto (join de asignaciones a cursos por curso_id, columna
`nivel`) y el resultado cuando el curso no tiene nivel definido, que es el
estado de todos los cursos existentes antes de la funcionalidad de nivel
academico.
"""
from app.services.asignacion_academica import (
    resolver_nivel_curso_cursor,
    resolver_nivel_y_materia_cursor,
)


class CursorFalso:
    def __init__(self, fila=None):
        self.fila = fila
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila


def test_resuelve_el_nivel_del_curso_de_la_asignacion():
    cursor = CursorFalso(fila=("preescolar",))

    nivel = resolver_nivel_curso_cursor(cursor, 12)

    query, params = cursor.calls[0]
    assert "SELECT c.nivel" in query
    assert "FROM asignaciones a" in query
    assert "JOIN cursos c ON c.id = a.curso_id" in query
    assert "WHERE a.id = %s" in query
    assert params == (12,)
    assert nivel == "preescolar"


def test_devuelve_none_si_el_curso_no_tiene_nivel_definido():
    cursor = CursorFalso(fila=(None,))

    assert resolver_nivel_curso_cursor(cursor, 12) is None


def test_devuelve_none_si_la_asignacion_no_existe():
    cursor = CursorFalso(fila=None)

    assert resolver_nivel_curso_cursor(cursor, 999) is None


def test_resuelve_el_nivel_y_la_materia_de_la_asignacion():
    cursor = CursorFalso(fila=("preescolar", "ASISTENCIA DIARIA"))

    nivel, materia = resolver_nivel_y_materia_cursor(cursor, 12)

    query, params = cursor.calls[0]
    assert "SELECT c.nivel, m.nombre" in query
    assert "FROM asignaciones a" in query
    assert "JOIN cursos c ON c.id = a.curso_id" in query
    assert "JOIN materias m ON m.id = a.materia_id" in query
    assert "WHERE a.id = %s" in query
    assert params == (12,)
    assert (nivel, materia) == ("preescolar", "ASISTENCIA DIARIA")


def test_nivel_y_materia_devuelve_none_none_si_la_asignacion_no_existe():
    cursor = CursorFalso(fila=None)

    assert resolver_nivel_y_materia_cursor(cursor, 999) == (None, None)
