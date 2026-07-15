from datetime import date

import pytest
from pydantic import ValidationError

from app.controllers import planeador_anual_controller
from app.schemas.planeador_anual import PlaneadorAnualUpdate


def test_fila_vacia_normaliza_fecha_vacia_a_none():
    fila = PlaneadorAnualUpdate(fecha="")

    assert fila.fecha is None
    assert fila.unidad_tematica == ""


def test_fila_permite_un_campo_si_tiene_fecha_limite():
    fila = PlaneadorAnualUpdate(
        contenido="  Fracciones equivalentes  ",
        fecha="2026-08-15",
    )

    assert fila.contenido == "Fracciones equivalentes"
    assert fila.fecha == date(2026, 8, 15)


def test_fila_rechaza_contenido_sin_fecha_limite():
    with pytest.raises(ValidationError, match="fecha límite"):
        PlaneadorAnualUpdate(unidad_tematica="Números enteros")


def test_fila_rechaza_fecha_sin_contenido():
    with pytest.raises(ValidationError, match="campo de contenido"):
        PlaneadorAnualUpdate(fecha="2026-08-15")


class FakeCursor:
    def __init__(self):
        self.calls = []
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_bulk_elimina_filas_vacias_y_conserva_slot_de_filas_diligenciadas(monkeypatch):
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    filas = [
        PlaneadorAnualUpdate(),
        PlaneadorAnualUpdate(contenido="Fracciones", fecha="2026-08-15"),
    ]

    monkeypatch.setattr(planeador_anual_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        planeador_anual_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 77,
    )

    planeador_anual_controller.bulk_actualizar_planeadores_controller(10, 2, filas)

    delete_query, delete_params = cursor.calls[0]
    insert_query, insert_params = cursor.calls[1]
    assert "DELETE FROM planeador_anual" in delete_query
    assert delete_params == (77, 2, 1)
    assert "INSERT INTO planeador_anual" in insert_query
    assert insert_params == (77, 2, 2, "", "", "Fracciones", "", date(2026, 8, 15))
    assert conn.committed is True
    assert conn.rolled_back is False
    assert cursor.closed is True
    assert conn.closed is True
