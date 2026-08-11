"""Caracterizacion de los servicios de validacion migrados en la subcapa 1.2.

Fijan el comportamiento observable: que sentencia y parametros se ejecutan, y que
la funcion devuelve True o False segun haya fila. Son las mismas garantias que
ofrecia la version anterior con get_connection, de modo que protegen la migracion
al regimen de get_cursor.
"""

from contextlib import contextmanager

import pytest

from app.services import nota_service, planilla_service


class CursorFalso:
    def __init__(self, fila):
        self.fila = fila
        self.ejecutados = []

    def execute(self, sentencia, parametros=None):
        self.ejecutados.append((sentencia, parametros))

    def fetchone(self):
        return self.fila


@pytest.fixture
def cursor_de(monkeypatch):
    def instalar(modulo, fila):
        cursor = CursorFalso(fila)

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            yield cursor

        monkeypatch.setattr(modulo, "get_cursor", fake_get_cursor)
        return cursor

    return instalar


def test_validar_asignacion_devuelve_true_si_existe(cursor_de):
    cursor = cursor_de(nota_service, (7,))

    assert nota_service.validar_asignacion(7) is True

    sentencia, parametros = cursor.ejecutados[0]
    assert "FROM asignaciones" in sentencia
    assert parametros == (7,)


def test_validar_asignacion_devuelve_false_si_no_existe(cursor_de):
    cursor_de(nota_service, None)

    assert nota_service.validar_asignacion(7) is False


def test_validar_estudiante_devuelve_true_si_existe(cursor_de):
    cursor = cursor_de(nota_service, (3,))

    assert nota_service.validar_estudiante(3) is True

    sentencia, parametros = cursor.ejecutados[0]
    assert "FROM estudiantes" in sentencia
    assert parametros == (3,)


def test_validar_estudiante_devuelve_false_si_no_existe(cursor_de):
    cursor_de(nota_service, None)

    assert nota_service.validar_estudiante(3) is False


def test_validar_estudiante_en_curso_cruza_curso_de_la_asignacion(cursor_de):
    cursor = cursor_de(nota_service, (3,))

    assert nota_service.validar_estudiante_en_curso(3, 7) is True

    sentencia, parametros = cursor.ejecutados[0]
    assert "JOIN asignaciones a ON e.curso_id = a.curso_id" in sentencia
    assert parametros == (3, 7)


def test_validar_estudiante_en_curso_devuelve_false_si_no_pertenece(cursor_de):
    cursor_de(nota_service, None)

    assert nota_service.validar_estudiante_en_curso(3, 7) is False


def test_validar_estudiante_asignacion_cruza_curso_de_la_asignacion(cursor_de):
    cursor = cursor_de(planilla_service, (3,))

    assert planilla_service.validar_estudiante_asignacion(3, 7) is True

    sentencia, parametros = cursor.ejecutados[0]
    assert "JOIN asignaciones a ON e.curso_id = a.curso_id" in sentencia
    assert parametros == (3, 7)


def test_validar_estudiante_asignacion_devuelve_false_si_no_pertenece(cursor_de):
    cursor_de(planilla_service, None)

    assert planilla_service.validar_estudiante_asignacion(3, 7) is False
