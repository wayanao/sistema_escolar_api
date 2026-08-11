"""Caracterizacion del controlador de inventario migrado en la subcapa 1.4e.

Cubre las tres funciones que pasaron de get_connection a get_cursor.

Ademas del SQL y del commit, se fija la aritmetica de _formatear_producto, que
calcula utilidad y margen. Son cifras que el frontend muestra como dinero, asi
que cualquier cambio ahi seria visible para el usuario final.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import inventario_controller


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

        monkeypatch.setattr(inventario_controller, "get_cursor", fake_get_cursor)
        return cursor, commits

    return instalar


def test_obtener_inventario_filtra_por_estado_activo_por_defecto(cursor_de):
    cursor, commits = cursor_de(filas=[(1, "Cuaderno", 1000, 1500, 4, "activo")])

    resultado = inventario_controller.obtener_inventario_controller()

    query, params = cursor.calls[0]
    assert "WHERE COALESCE(LOWER(estado), 'activo') = %s" in query
    assert "ORDER BY nombre" in query
    assert params == ["activo"]
    assert commits == [False]
    assert resultado[0]["nombre"] == "Cuaderno"


def test_obtener_inventario_con_todos_no_agrega_filtro(cursor_de):
    cursor, _ = cursor_de(filas=[])

    inventario_controller.obtener_inventario_controller(estado="todos")

    query, params = cursor.calls[0]
    assert "WHERE" not in query
    assert params == []


def test_obtener_inventario_normaliza_un_estado_desconocido(cursor_de):
    cursor, _ = cursor_de(filas=[])

    inventario_controller.obtener_inventario_controller(estado="descatalogado")

    _, params = cursor.calls[0]
    assert params == ["activo"]


def test_obtener_inventario_calcula_utilidad_y_margen(cursor_de):
    cursor_de(filas=[(1, "Cuaderno", 1000, 1500, 4, "activo")])

    producto = inventario_controller.obtener_inventario_controller()[0]

    assert producto["costo"] == 1000.0
    assert producto["precio_venta"] == 1500.0
    assert producto["stock_actual"] == 4
    assert producto["utilidad_unitaria"] == 500.0
    assert producto["utilidad_total_proyectada"] == 2000.0
    assert producto["margen_utilidad"] == 33.33


def test_obtener_inventario_evita_dividir_por_cero_si_el_precio_es_cero(cursor_de):
    cursor_de(filas=[(2, "Muestra", 0, 0, 1, "activo")])

    producto = inventario_controller.obtener_inventario_controller()[0]

    assert producto["margen_utilidad"] == 0
    assert producto["utilidad_unitaria"] == 0.0


def test_crear_inventario_inserta_confirmando_y_devuelve_el_id(cursor_de):
    cursor, commits = cursor_de(fila=(15,))
    producto = SimpleNamespace(
        nombre="Cuaderno", costo=1000, precio_venta=1500,
        stock_actual=4, estado="activo",
    )

    assert inventario_controller.crear_inventario_controller(producto) == 15

    query, params = cursor.calls[0]
    assert "INSERT INTO inventario" in query
    assert "RETURNING id" in query
    assert params == ("Cuaderno", 1000, 1500, 4, "activo")
    assert commits == [True]


def test_crear_inventario_normaliza_un_estado_invalido(cursor_de):
    cursor, _ = cursor_de(fila=(15,))
    producto = SimpleNamespace(
        nombre="Cuaderno", costo=1000, precio_venta=1500,
        stock_actual=4, estado="agotado",
    )

    inventario_controller.crear_inventario_controller(producto)

    _, params = cursor.calls[0]
    assert params[-1] == "activo"


def test_actualizar_inventario_confirma_el_cambio(cursor_de):
    cursor, commits = cursor_de()
    producto = SimpleNamespace(
        nombre="Cuaderno grande", costo=1200, precio_venta=1800,
        stock_actual=9, estado="inactivo",
    )

    inventario_controller.actualizar_inventario_controller(15, producto)

    query, params = cursor.calls[0]
    assert "UPDATE inventario" in query
    assert params == ("Cuaderno grande", 1200, 1800, 9, "inactivo", 15)
    assert commits == [True]
