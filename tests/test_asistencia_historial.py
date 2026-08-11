"""Caracterizacion de obtener_historial_asistencia, migrada en la subcapa 1.4g.

Es la unica funcion desprotegida que quedaba en asistencia_controller;
guardar_asistencia_controller ya tenia try/finally y no se toco.

La funcion agrupa las filas por estudiante, asi que una misma persona con varias
fechas debe aparecer una sola vez con su historial completo. Y un estudiante cuya
fila trae fecha nula aparece igual, con historial vacio: ese comportamiento es
previo a la migracion y se conserva.
"""

from contextlib import contextmanager
from datetime import date

import pytest

from app.controllers import asistencia_controller


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
    def instalar(filas=(), asignacion_resuelta=77):
        cursor = CursorFalso(filas)
        commits = []
        resueltos = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        def fake_resolver(_cursor, asignacion_id):
            resueltos.append(asignacion_id)
            return asignacion_resuelta

        monkeypatch.setattr(asistencia_controller, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            asistencia_controller,
            "resolver_asignacion_academica_id_cursor",
            fake_resolver,
        )
        return cursor, commits, resueltos

    return instalar


def test_historial_resuelve_la_asignacion_y_consulta_el_periodo(cursor_de):
    cursor, commits, resueltos = cursor_de(
        filas=[(11, "Ana", "Ríos", date(2026, 8, 3), "ausente")]
    )

    asistencia_controller.obtener_historial_asistencia(12, periodo=2)

    query, params = cursor.calls[0]
    assert "FROM estudiantes e" in query
    assert "JOIN asistencia a ON a.estudiante_id = e.id" in query
    assert "WHERE a.asignacion_id = %s AND a.periodo = %s" in query
    assert params == (77, 2)
    assert resueltos == [12]
    assert commits == [False]


def test_historial_agrupa_varias_fechas_del_mismo_estudiante(cursor_de):
    cursor_de(filas=[
        (11, "Ana", "Ríos", date(2026, 8, 3), "ausente"),
        (11, "Ana", "Ríos", date(2026, 8, 5), "presente"),
        (12, "Beto", "Sáenz", date(2026, 8, 3), "presente"),
    ])

    resultado = asistencia_controller.obtener_historial_asistencia(12)

    assert resultado == [
        {
            "estudiante_id": 11,
            "nombre": "Ana",
            "apellido": "Ríos",
            "historial": [
                {"fecha": "2026-08-03", "estado": "ausente"},
                {"fecha": "2026-08-05", "estado": "presente"},
            ],
        },
        {
            "estudiante_id": 12,
            "nombre": "Beto",
            "apellido": "Sáenz",
            "historial": [{"fecha": "2026-08-03", "estado": "presente"}],
        },
    ]


def test_historial_incluye_al_estudiante_aunque_la_fecha_sea_nula(cursor_de):
    cursor_de(filas=[(11, "Ana", "Ríos", None, "ausente")])

    resultado = asistencia_controller.obtener_historial_asistencia(12)

    assert resultado == [{
        "estudiante_id": 11,
        "nombre": "Ana",
        "apellido": "Ríos",
        "historial": [],
    }]


def test_historial_usa_periodo_uno_por_defecto(cursor_de):
    cursor, _, _ = cursor_de(filas=[])

    asistencia_controller.obtener_historial_asistencia(12)

    _, params = cursor.calls[0]
    assert params == (77, 1)


def test_historial_sin_filas_devuelve_lista_vacia(cursor_de):
    cursor_de(filas=[])

    assert asistencia_controller.obtener_historial_asistencia(12) == []
