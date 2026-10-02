from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace

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


PROFESOR = {"id": 3, "rol": "profesor"}


@pytest.fixture(autouse=True)
def guardia_del_anio(monkeypatch):
    """Año lectivo, paso 3.7: la guardia de escritura se dobla aqui, igual que
    el resolutor. Sus pruebas viven en `test_anio_lectivo_guardia.py` y la
    cuenta `test_anio_lectivo_guardia_conteos.py`."""
    llamadas = []
    monkeypatch.setattr(
        planeador_anual_controller,
        "exigir_asignacion_editable",
        lambda _cursor, asignacion_id, usuario: llamadas.append((asignacion_id, usuario)),
    )
    return llamadas


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

    planeador_anual_controller.bulk_actualizar_planeadores_controller(10, 2, filas, usuario=PROFESOR)

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


# Caracterizacion de las tres funciones migradas a get_cursor en la subcapa 1.3.
# La asercion sobre `commit` es la que importa: si se perdiera, get_cursor
# revertiria al cerrar y los datos se descartarian en silencio.


class CursorMigrado:
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
def cursor_migrado(monkeypatch):
    def instalar(fila=None, filas=None):
        cursor = CursorMigrado(fila=fila, filas=filas)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        monkeypatch.setattr(planeador_anual_controller, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            planeador_anual_controller,
            "resolver_asignacion_academica_id_cursor",
            lambda _cursor, _asignacion_id: 77,
        )
        return cursor, commits

    return instalar


def test_crear_planeador_inserta_confirmando_y_devuelve_el_id(cursor_migrado):
    cursor, commits = cursor_migrado(fila=(501,))
    planeador = SimpleNamespace(
        asignacion_id=10,
        periodo=2,
        slot=1,
        unidad_tematica="Números enteros",
        estandar_competencia="Comprende",
        contenido="Suma y resta",
        actividades_recursos="Guía",
        fecha=date(2026, 8, 15),
    )

    assert planeador_anual_controller.crear_planeador_anual_controller(planeador) == 501

    query, params = cursor.calls[0]
    assert "INSERT INTO planeador_anual" in query
    assert "RETURNING id" in query
    assert params[0] == 77
    assert params[1:] == (
        2,
        1,
        "Números enteros",
        "Comprende",
        "Suma y resta",
        "Guía",
        date(2026, 8, 15),
    )
    assert commits == [True]


def test_obtener_planeadores_consulta_sin_confirmar(cursor_migrado):
    fila = (1, 77, 2, 3, "Unidad", "Estandar", "Contenido", "Recursos", date(2026, 8, 15))
    cursor, commits = cursor_migrado(filas=[fila])

    resultado = planeador_anual_controller.obtener_planeadores_anual_controller(10, 2)

    query, params = cursor.calls[0]
    assert "FROM planeador_anual" in query
    assert "ORDER BY slot" in query
    assert params == (77, 2)
    assert commits == [False]
    assert resultado == [
        {
            "id": 1,
            "asignacion_id": 77,
            "periodo": 2,
            "slot": 3,
            "unidad_tematica": "Unidad",
            "estandar_competencia": "Estandar",
            "contenido": "Contenido",
            "actividades_recursos": "Recursos",
            "fecha": date(2026, 8, 15),
        }
    ]


def test_actualizar_planeador_actualiza_confirmando(cursor_migrado):
    cursor, commits = cursor_migrado()
    planeador = PlaneadorAnualUpdate(contenido="Fracciones", fecha="2026-08-15")

    planeador_anual_controller.actualizar_planeador_anual_controller(42, planeador)

    query, params = cursor.calls[0]
    assert "UPDATE planeador_anual" in query
    assert params == ("", "", "Fracciones", "", date(2026, 8, 15), 42)
    assert commits == [True]
