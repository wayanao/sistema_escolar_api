"""Caracterizacion del controlador de notas migrado en la subcapa 1.4h.

Las cinco funciones del archivo estaban desprotegidas y ninguna tenia cobertura.
Las pruebas existentes de notas cubren permisos en la ruta, no estos calculos.

Se fija lo que el usuario final ve como calificaciones:
- el promedio y su redondeo, incluido el caso sin notas;
- el corte Aprobado/Reprobado en 3.0;
- las tres actividades en blanco que el boletin detallado fabrica cuando no hay
  calificaciones, con sus ids sinteticos por concatenacion de cadenas;
- que las validaciones de crear_nota devuelvan error sin pedir conexion.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import notas_controller


class CursorFalso:
    """Devuelve un resultado distinto por cada fetchall, en orden."""

    def __init__(self, resultados=(), fila=None):
        self.resultados = list(resultados)
        self.fila = fila
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila

    def fetchall(self):
        return self.resultados.pop(0) if self.resultados else []


@pytest.fixture
def cursor_de(monkeypatch):
    def instalar(resultados=(), fila=None, asignacion_resuelta=77):
        cursor = CursorFalso(resultados=resultados, fila=fila)
        commits = []
        resueltos = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        def fake_resolver(_cursor, asignacion_id):
            resueltos.append(asignacion_id)
            return asignacion_resuelta

        monkeypatch.setattr(notas_controller, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            notas_controller, "resolver_asignacion_academica_id_cursor", fake_resolver
        )
        return cursor, commits, resueltos

    return instalar


@pytest.fixture
def validaciones_ok(monkeypatch):
    monkeypatch.setattr(notas_controller, "validar_asignacion", lambda _id: True)
    monkeypatch.setattr(notas_controller, "validar_estudiante", lambda _id: True)
    monkeypatch.setattr(notas_controller, "validar_estudiante_en_curso", lambda _e, _a: True)


NOTA = SimpleNamespace(asignacion_id=12, estudiante_id=11, nota=4.2, descripcion="Parcial 1")
ADMIN = {"id": 1, "rol": "admin"}


@pytest.fixture(autouse=True)
def guardia_del_anio(monkeypatch):
    """Año lectivo, paso 3.7: la guardia de escritura se dobla aqui, igual que
    el resolutor de la asignacion academica, asi que no suma en los conteos de
    este archivo (en produccion es una consulta mas; la cuenta
    `test_anio_lectivo_guardia_conteos.py`). Sus pruebas viven en
    `test_anio_lectivo_guardia.py`; aqui solo se anota a quien se le pidio."""
    llamadas = []
    monkeypatch.setattr(
        notas_controller,
        "exigir_asignacion_editable",
        lambda _cursor, asignacion_id, usuario: llamadas.append((asignacion_id, usuario)),
    )
    return llamadas


def test_crear_nota_inserta_confirmando(cursor_de, validaciones_ok, guardia_del_anio):
    cursor, commits, resueltos = cursor_de(fila=(501,))

    respuesta = notas_controller.crear_nota_controller(NOTA, usuario=ADMIN)

    query, params = cursor.calls[0]
    assert "INSERT INTO notas_detalle" in query
    assert "RETURNING id" in query
    assert params == (11, 77, 4.2, "Parcial 1")
    assert resueltos == [12]
    assert guardia_del_anio == [(12, ADMIN)]
    assert commits == [True]
    assert respuesta == {"mensaje": "Nota creada", "id": 501}


@pytest.mark.parametrize(
    "validador,mensaje",
    [
        ("validar_asignacion", "La asignación no existe"),
        ("validar_estudiante", "El estudiante no existe"),
        ("validar_estudiante_en_curso", "El estudiante no pertenece a ese curso"),
    ],
)
def test_crear_nota_rechaza_sin_pedir_conexion(
    cursor_de, validaciones_ok, monkeypatch, validador, mensaje, guardia_del_anio
):
    cursor, commits, _ = cursor_de()
    monkeypatch.setattr(notas_controller, validador, lambda *_args: False)

    respuesta = notas_controller.crear_nota_controller(NOTA, usuario=ADMIN)

    assert respuesta == {"error": mensaje}
    assert cursor.calls == []
    assert commits == []
    assert guardia_del_anio == []


def test_notas_estudiante_calcula_el_promedio(cursor_de):
    cursor, commits, _ = cursor_de(resultados=[[(4.0, "Parcial 1"), (3.0, "Parcial 2")]])

    respuesta = notas_controller.notas_estudiante_controller(11)

    query, params = cursor.calls[0]
    assert "FROM notas_detalle nd" in query
    assert params == (11,)
    assert commits == [False]
    assert respuesta == {
        "notas": [
            {"nota": 4.0, "descripcion": "Parcial 1"},
            {"nota": 3.0, "descripcion": "Parcial 2"},
        ],
        "promedio": 3.5,
    }


def test_notas_estudiante_sin_notas_devuelve_promedio_cero(cursor_de):
    cursor_de(resultados=[[]])

    respuesta = notas_controller.notas_estudiante_controller(11)

    assert respuesta == {"notas": [], "promedio": 0}


def test_boletin_estudiante_marca_aprobado_desde_tres(cursor_de):
    filas = [
        ("Ana", "Ríos", "Quinto A", "Matemáticas", 3.0),
        ("Ana", "Ríos", "Quinto A", "Lenguaje", 2.0),
    ]
    cursor, commits, _ = cursor_de(resultados=[filas])

    respuesta = notas_controller.boletin_estudiante_controller(11)

    assert commits == [False]
    assert respuesta["nombre"] == "Ana"
    assert respuesta["curso"] == "Quinto A"
    assert respuesta["materias"] == [
        {"materia": "Matemáticas", "promedio": 3.0, "estado": "Aprobado"},
        {"materia": "Lenguaje", "promedio": 2.0, "estado": "Reprobado"},
    ]
    assert respuesta["promedio_general"] == 2.5
    assert respuesta["estado_final"] == "Reprobado"


def test_boletin_estudiante_sin_filas_avisa_que_no_existe(cursor_de):
    cursor_de(resultados=[[]])

    assert notas_controller.boletin_estudiante_controller(11) == {
        "mensaje": "Estudiante no encontrado"
    }


def test_planilla_asignacion_resuelve_y_redondea(cursor_de):
    filas = [(11, "Ana", "Ríos", "Matemáticas", "Quinto A", 3.456)]
    cursor, commits, resueltos = cursor_de(resultados=[filas])

    respuesta = notas_controller.planilla_asignacion_controller(12)

    query, params = cursor.calls[0]
    assert "COALESCE(LOWER(e.estado), 'activo') = 'activo'" in query
    assert params == (77,)
    assert resueltos == [12]
    assert commits == [False]
    assert respuesta == [{
        "estudiante_id": 11,
        "nombre": "Ana",
        "apellido": "Ríos",
        "materia": "Matemáticas",
        "curso": "Quinto A",
        "promedio": 3.46,
    }]


def test_boletin_detallado_usa_las_notas_guardadas(cursor_de):
    asignaciones = [(5, "Matemáticas", "Ana Ríos", 77)]
    notas = [(901, "Parcial 1", 4.0)]
    cursor, commits, _ = cursor_de(resultados=[asignaciones, notas])

    respuesta = notas_controller.boletin_detallado_controller(11, periodo=2)

    _, params_notas = cursor.calls[1]
    assert params_notas == (11, 77, 2)
    assert commits == [False]
    assert respuesta == [{
        "id": 5,
        "asignacion_id": 77,
        "area": "Matemáticas",
        "docente": "Ana Ríos",
        "actividades": [{"id": 901, "descripcion": "Parcial 1", "nota": 4.0}],
        "promedio": 0,
    }]


def test_boletin_detallado_fabrica_tres_actividades_si_no_hay_notas(cursor_de):
    asignaciones = [(5, "Matemáticas", "Ana Ríos", 77)]
    cursor_de(resultados=[asignaciones, []])

    respuesta = notas_controller.boletin_detallado_controller(11)

    # Los ids se arman concatenando el id de materia con 01, 02 y 03.
    assert respuesta[0]["actividades"] == [
        {"id": 501, "descripcion": "Actividad 1", "nota": 0.0},
        {"id": 502, "descripcion": "Actividad 2", "nota": 0.0},
        {"id": 503, "descripcion": "Actividad 3", "nota": 0.0},
    ]


def test_boletin_detallado_consulta_una_vez_por_asignacion(cursor_de):
    asignaciones = [
        (5, "Matemáticas", "Ana Ríos", 77),
        (6, "Lenguaje", "Beto Sáenz", 78),
    ]
    cursor, _, _ = cursor_de(resultados=[asignaciones, [], []])

    respuesta = notas_controller.boletin_detallado_controller(11)

    # Una consulta de asignaciones mas una por cada una: patron N+1 conservado.
    assert len(cursor.calls) == 3
    assert len(respuesta) == 2


def test_boletin_detallado_sin_asignaciones_devuelve_lista_vacia(cursor_de):
    cursor, _, _ = cursor_de(resultados=[[]])

    assert notas_controller.boletin_detallado_controller(11) == []
    assert len(cursor.calls) == 1


def test_boletin_detallado_usa_periodo_uno_por_defecto(cursor_de):
    asignaciones = [(5, "Matemáticas", "Ana Ríos", 77)]
    cursor, _, _ = cursor_de(resultados=[asignaciones, []])

    notas_controller.boletin_detallado_controller(11)

    _, params_notas = cursor.calls[1]
    assert params_notas == (11, 77, 1)
