"""Caracterizacion del dominio planilla migrado en la subcapa 1.4j.

Cubre los tres sitios: los dos de planilla_controller y el de
planilla_excel_controller.

Lo que mas importa fijar:
- registrar_nota_planilla_controller borra e inserta en la MISMA transaccion.
  Ese par evita notas duplicadas para la misma descripcion; separarlo permitiria
  perder la nota anterior sin escribir la nueva.
- planilla_excel_controller descarta la descripcion "Desde React", una cadena
  magica heredada, y devuelve el promedio como CADENA VACIA cuando el estudiante
  no tiene ninguna nota numerica.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import planilla_controller, planilla_excel_controller


class CursorFalso:
    def __init__(self, fila=None, filas=()):
        self.fila = fila
        self.filas = list(filas)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila

    def fetchall(self):
        return self.filas


def _instalador(modulo, monkeypatch):
    def instalar(fila=None, filas=(), asignacion_resuelta=77):
        cursor = CursorFalso(fila=fila, filas=filas)
        commits = []
        resueltos = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        def fake_resolver(_cursor, asignacion_id):
            resueltos.append(asignacion_id)
            return asignacion_resuelta

        monkeypatch.setattr(modulo, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            modulo, "resolver_asignacion_academica_id_cursor", fake_resolver
        )
        return cursor, commits, resueltos

    return instalar


@pytest.fixture
def cursor_planilla(monkeypatch):
    monkeypatch.setattr(
        planilla_controller, "validar_estudiante_asignacion", lambda _e, _a: True
    )
    return _instalador(planilla_controller, monkeypatch)


@pytest.fixture
def cursor_excel(monkeypatch):
    return _instalador(planilla_excel_controller, monkeypatch)


DATOS = SimpleNamespace(
    estudiante_id=11,
    asignacion_id=12,
    periodo=2,
    nota=4.5,
    descripcion="  Parcial 1  ",
    tipo_evaluacion="numerica",
    valoracion=None,
)


def test_registrar_nota_borra_y_reinserta_en_la_misma_transaccion(cursor_planilla):
    cursor, commits, resueltos = cursor_planilla(fila=(901,))

    respuesta = planilla_controller.registrar_nota_planilla_controller(DATOS)

    borrado, params_borrado = cursor.calls[0]
    insercion, params_insercion = cursor.calls[1]
    assert "DELETE FROM notas_detalle" in borrado
    assert params_borrado == (11, 77, 2, "  Parcial 1  ")
    assert "INSERT INTO notas_detalle" in insercion
    assert "TRIM(%s)" in insercion
    assert params_insercion == (11, 77, 2, 4.5, "  Parcial 1  ", "numerica", None)
    # Un solo bloque para el par borrar/insertar: si se partiera, un fallo entre
    # ambos dejaria al estudiante sin la nota anterior ni la nueva.
    assert commits == [True]
    assert resueltos == [12]
    assert respuesta == {"mensaje": "Nota registrada correctamente", "nota_id": 901}


def test_registrar_nota_de_desarrollo_guarda_valoracion_y_no_nota(cursor_planilla):
    cursor, _, _ = cursor_planilla(fila=(902,))
    datos = SimpleNamespace(
        estudiante_id=11, asignacion_id=12, periodo=1, nota=4.5,
        descripcion="Ensayo", tipo_evaluacion="desarrollo", valoracion="Alto",
    )

    planilla_controller.registrar_nota_planilla_controller(datos)

    _, params = cursor.calls[1]
    assert params[3] is None
    assert params[5] == "desarrollo"
    assert params[6] == "Alto"


def test_registrar_nota_rechaza_estudiante_ajeno_sin_pedir_conexion(cursor_planilla, monkeypatch):
    cursor, commits, _ = cursor_planilla()
    monkeypatch.setattr(
        planilla_controller, "validar_estudiante_asignacion", lambda _e, _a: False
    )

    respuesta = planilla_controller.registrar_nota_planilla_controller(DATOS)

    assert respuesta == {"error": "El estudiante no pertenece a esta asignación"}
    assert cursor.calls == []
    assert commits == []


def test_eliminar_tipo_borra_la_columna_del_periodo(cursor_planilla):
    cursor, commits, resueltos = cursor_planilla()

    respuesta = planilla_controller.eliminar_tipo_controller(12, "Parcial 1", periodo=3)

    query, params = cursor.calls[0]
    assert "DELETE FROM notas_detalle" in query
    assert "LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))" in query
    assert params == (77, 3, "Parcial 1")
    assert resueltos == [12]
    assert commits == [True]
    assert respuesta == {"mensaje": "Tipo eliminado correctamente"}


def test_eliminar_tipo_usa_periodo_uno_por_defecto(cursor_planilla):
    cursor, _, _ = cursor_planilla()

    planilla_controller.eliminar_tipo_controller(12, "Parcial 1")

    _, params = cursor.calls[0]
    assert params == (77, 1, "Parcial 1")


def test_excel_agrupa_notas_por_estudiante_y_calcula_promedio(cursor_excel):
    filas = [
        (11, "Ana", "Ríos", "Matemáticas", "Parcial 1", 4.0, "numerica", None),
        (11, "Ana", "Ríos", "Matemáticas", "Parcial 2", 3.0, "numerica", None),
    ]
    cursor, commits, resueltos = cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12, periodo=2)

    _, params = cursor.calls[0]
    assert params == (2, 77)
    assert resueltos == [12]
    assert commits == [False]
    assert resultado["columnas"] == ["Parcial 1", "Parcial 2"]
    assert resultado["data"][0]["promedio"] == 3.5
    assert resultado["data"][0]["notas"] == {"Parcial 1": 4.0, "Parcial 2": 3.0}


def test_excel_descarta_la_descripcion_heredada_desde_react(cursor_excel):
    filas = [(11, "Ana", "Ríos", "Matemáticas", "Desde React", 4.0, "numerica", None)]
    cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12)

    assert resultado["columnas"] == []
    assert resultado["data"][0]["notas"] == {}


def test_excel_devuelve_promedio_como_cadena_vacia_si_no_hay_notas_numericas(cursor_excel):
    filas = [(11, "Ana", "Ríos", "Matemáticas", "Ensayo", None, "desarrollo", "Alto")]
    cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12)

    assert resultado["data"][0]["promedio"] == ""
    assert resultado["data"][0]["valoraciones"] == {"Ensayo": "Alto"}


def test_excel_excluye_las_de_desarrollo_del_promedio(cursor_excel):
    filas = [
        (11, "Ana", "Ríos", "Matemáticas", "Parcial 1", 4.0, "numerica", None),
        (11, "Ana", "Ríos", "Matemáticas", "Ensayo", 1.0, "desarrollo", "Alto"),
    ]
    cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12)

    assert resultado["data"][0]["promedio"] == 4.0


def test_excel_ordena_por_apellido_y_nombre(cursor_excel):
    filas = [
        (12, "Beto", "Sáenz", "Matemáticas", "Parcial 1", 3.0, "numerica", None),
        (11, "Ana", "Ríos", "Matemáticas", "Parcial 1", 4.0, "numerica", None),
    ]
    cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12)

    assert [e["apellido"] for e in resultado["data"]] == ["Ríos", "Sáenz"]
