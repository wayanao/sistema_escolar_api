"""Caracterizacion del controlador de dashboard migrado en la subcapa 1.4d.

Cubre las cuatro funciones que pasaron de get_connection a get_cursor. Las cuatro
son de solo lectura, asi que ninguna confirma.

La mas delicada es _obtener_notas_profesor, que arma el SQL de forma dinamica:
cambia el comparador y el orden segun se pidan notas altas o bajas, y agrega un
filtro solo cuando recibe asignacion_id. Son cuatro combinaciones y todas se
fijan aqui, junto al color que asigna a cada fila.
"""

from contextlib import contextmanager

import pytest

from app.controllers import dashboard_controller


class CursorFalso:
    def __init__(self, filas):
        self.filas = filas
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchall(self):
        return self.filas


@pytest.fixture
def cursor_de(monkeypatch):
    def instalar(filas=(), asignacion_resuelta=77):
        cursor = CursorFalso(list(filas))
        commits = []
        resueltos = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        def fake_resolver(_cursor, asignacion_id):
            resueltos.append(asignacion_id)
            return asignacion_resuelta

        monkeypatch.setattr(dashboard_controller, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            dashboard_controller,
            "resolver_asignacion_academica_id_cursor",
            fake_resolver,
        )
        return cursor, commits, resueltos

    return instalar


def test_inasistencias_limita_a_los_tres_primeros_por_curso(cursor_de):
    fila = (4, "Quinto A", 11, "Ana Ríos", 6, 1)
    cursor, commits, _ = cursor_de(filas=[fila])

    resultado = dashboard_controller.obtener_inasistencias_profesor_controller(9)

    query, params = cursor.calls[0]
    assert "WHERE posicion_curso <= 3" in query
    assert "a.estado ILIKE 'ausente'" in query
    assert params == (9,)
    assert commits == [False]
    assert resultado == [{
        "curso_id": 4,
        "curso": "Quinto A",
        "estudiante_id": 11,
        "nombre": "Ana Ríos",
        "total_fallas": 6,
        "posicion": 1,
    }]


def test_notas_bajas_filtra_por_debajo_de_tres_y_ordena_ascendente(cursor_de):
    cursor, commits, resueltos = cursor_de(filas=[("Ana Ríos", "Quinto A", "Matemáticas", 2.5)])

    resultado = dashboard_controller.obtener_notas_bajas_profesor_controller(9, 4)

    query, params = cursor.calls[0]
    assert "HAVING TRUNC(AVG(promedio_clase), 2) < 3.0" in query
    assert "ORDER BY promedio ASC" in query
    assert "AND asi.id = %s" not in query
    assert params == (9, 4, None)
    assert resueltos == []
    assert commits == [False]
    assert resultado == [{
        "nombre": "Ana Ríos",
        "curso": "Quinto A",
        "materia": "Matemáticas",
        "promedio": 2.5,
        "color": "red",
    }]


def test_notas_altas_filtra_desde_tres_y_ordena_descendente(cursor_de):
    cursor, _, _ = cursor_de(filas=[("Ana Ríos", "Quinto A", "Matemáticas", 4.5)])

    resultado = dashboard_controller.obtener_notas_altas_profesor_controller(9, 4)

    query, _ = cursor.calls[0]
    assert "HAVING TRUNC(AVG(promedio_clase), 2) >= 3.0" in query
    assert "ORDER BY promedio DESC" in query
    assert resultado[0]["color"] == "green"


def test_notas_con_asignacion_resuelve_el_id_y_agrega_el_filtro(cursor_de):
    cursor, _, resueltos = cursor_de(filas=[], asignacion_resuelta=77)

    dashboard_controller.obtener_notas_bajas_profesor_controller(9, 4, asignacion_id=12)

    query, params = cursor.calls[0]
    assert "AND asi.id = %s" in query
    assert params == (9, 4, 77, 77)
    assert resueltos == [12]


def test_notas_reutilizan_una_asignacion_academica_ya_resuelta(cursor_de):
    cursor, _, resueltos = cursor_de(filas=[])

    dashboard_controller.obtener_notas_bajas_profesor_controller(
        9,
        4,
        asignacion_id=12,
        asignacion_academica_id=77,
    )

    _, params = cursor.calls[0]
    assert params == (9, 4, 77, 77)
    assert resueltos == []


def test_notas_bajas_marca_amarillo_cuando_el_promedio_no_baja_de_tres(cursor_de):
    cursor_de(filas=[("Ana Ríos", "Quinto A", "Matemáticas", 3.2)])

    resultado = dashboard_controller.obtener_notas_bajas_profesor_controller(9, 4)

    assert resultado[0]["color"] == "yellow"


def test_ranking_rendimiento_lista_los_promedios_bajos(cursor_de):
    cursor, commits, resueltos = cursor_de(filas=[(11, "Ana Ríos", 2.4)])

    resultado = dashboard_controller.obtener_ranking_rendimiento_controller(12, 2)

    query, params = cursor.calls[0]
    assert "HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) < 3.0" in query
    assert "ORDER BY promedio ASC" in query
    assert params == (77, 2)
    assert resueltos == [12]
    assert commits == [False]
    assert resultado == [{"id": 11, "nombre": "Ana Ríos", "promedio": 2.4}]


def test_ranking_mejor_rendimiento_lista_los_promedios_altos(cursor_de):
    cursor, commits, resueltos = cursor_de(filas=[(11, "Ana Ríos", 4.6)])

    resultado = dashboard_controller.obtener_ranking_mejor_rendimiento_controller(12, 2)

    query, params = cursor.calls[0]
    assert "HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) >= 3.0" in query
    assert "ORDER BY promedio DESC" in query
    assert params == (77, 2)
    assert resueltos == [12]
    assert commits == [False]
    assert resultado == [{"id": 11, "nombre": "Ana Ríos", "promedio": 4.6}]
