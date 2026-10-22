"""Porcentajes por tipo de nota, paso B2d: las lecturas de la nota del periodo (PB7).

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`, "Avance del paso B2". Con los
porcentajes de la clase activos, el boletin del admin sin definitiva guardada,
el reporte parcial y los dos rankings usan la nota ponderada en vez del
promedio simple. Sin porcentajes activos dan lo de hoy: lo fija
`test_porcentajes_planilla_caracterizacion.py` (paso B1).

**Solo notas numericas**: hoy ninguno de estos tres lugares cuenta las caritas
(el boletin del admin y el reporte parcial dejan vacia la nota de preescolar,
y los rankings promedian `nota`), asi que con porcentajes tampoco.

El cursor responde segun un fragmento del SQL y, a cualquier otra consulta,
"nada", igual que en B1.
"""
from contextlib import contextmanager
from decimal import Decimal

import pytest

from app.controllers import boletin_controller, dashboard_controller
from app.services import porcentajes_activos


class CursorGuionado:
    """Responde segun un fragmento del SQL y guarda todo lo que se ejecuta."""

    def __init__(self, guion=()):
        self.guion = guion
        self.consultas = []
        self._uno = None
        self._todos = []

    def execute(self, sql, params=None):
        texto = " ".join(str(sql).split())
        self.consultas.append((texto, params))
        self._uno, self._todos = None, []
        for fragmento, uno, todos in self.guion:
            if fragmento in texto:
                self._uno, self._todos = uno, list(todos)
                break

    def fetchone(self):
        return self._uno

    def fetchall(self):
        return list(self._todos)

    def close(self):
        pass

    def leyo(self, fragmento):
        return [params for texto, params in self.consultas if fragmento in texto]


class ConexionFalsa:
    def __init__(self, cursor):
        self.cursor_obj = cursor

    def cursor(self, **_kwargs):
        return self.cursor_obj

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


@pytest.fixture
def boletin(monkeypatch):
    def instalar(guion):
        cursor = CursorGuionado(guion)
        monkeypatch.setattr(boletin_controller, "get_connection", lambda: ConexionFalsa(cursor))
        return cursor

    return instalar


@pytest.fixture
def tablero(monkeypatch):
    def instalar(guion):
        cursor = CursorGuionado([("AS asignacion_academica_id", (77,), []), *guion])

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            yield cursor

        monkeypatch.setattr(dashboard_controller, "get_cursor", fake_get_cursor)
        return cursor

    return instalar


PORCENTAJES_VARIAS = "SELECT asignacion_id, tipo_nota, porcentaje FROM planilla_tipos_porcentaje"
TIPOS_VARIAS = "SELECT DISTINCT asignacion_id, descripcion FROM notas_detalle"
CELDAS_DEL_ESTUDIANTE = "SELECT asignacion_id, descripcion, nota, valoracion FROM notas_detalle"
PORCENTAJES_UNA = "SELECT tipo_nota, porcentaje FROM planilla_tipos_porcentaje"
TIPOS_UNA = "SELECT DISTINCT descripcion FROM notas_detalle"
CELDAS_DE_LA_CLASE = "AS nombre_estudiante, n.descripcion"
RANKING_DE_HOY = "TRUNC(AVG(CAST(n.nota AS numeric)), 2)"

PESOS = {"Cognitivo": 50, "Procedimental": 30, "Actitudinal": 20}


def _porcentajes(asignacion_id, pesos=PESOS):
    return [(asignacion_id, tipo, valor) for tipo, valor in pesos.items()]


def _tipos(asignacion_id, pesos=PESOS):
    return [(asignacion_id, tipo) for tipo in pesos]


# --------------------------------------------------------------------------
# El servicio que dice que clases tienen porcentajes activos
# --------------------------------------------------------------------------

def test_sin_clases_no_consulta_nada():
    cursor = CursorGuionado()

    assert porcentajes_activos.porcentajes_activos_de_asignaciones(cursor, [], 2) == {}
    assert cursor.consultas == []


def test_solo_devuelve_las_clases_con_porcentajes_activos():
    cursor = CursorGuionado([
        (PORCENTAJES_VARIAS, None, _porcentajes(44) + [(45, "Cognitivo", 60)]),
        (TIPOS_VARIAS, None, _tipos(44) + [(45, "Cognitivo"), (45, "Procedimental")]),
    ])

    activos = porcentajes_activos.porcentajes_activos_de_asignaciones(cursor, [44, 45, 46], 2)

    assert activos == {44: PESOS}
    assert cursor.leyo(PORCENTAJES_VARIAS) == [([44, 45, 46], 2)]
    # Los tipos solo de las clases que tienen algun porcentaje.
    assert cursor.leyo(TIPOS_VARIAS) == [([44, 45], 2)]


def test_sin_ningun_porcentaje_no_pregunta_por_los_tipos():
    cursor = CursorGuionado([(PORCENTAJES_VARIAS, None, [])])

    assert porcentajes_activos.porcentajes_activos_de_asignaciones(cursor, [44], 2) == {}
    assert cursor.leyo(TIPOS_VARIAS) == []


# --------------------------------------------------------------------------
# Boletin del admin sin definitiva guardada
# --------------------------------------------------------------------------

def _materia(asignacion_id, nombre, definitiva, boletin_id=None):
    return {
        "asignacion_id": asignacion_id, "materia_id": asignacion_id + 100, "materia": nombre,
        "profesor_nombre": "Ana", "profesor_apellido": "Ruiz",
        "definitiva": definitiva, "boletin_id": boletin_id, "orden_boletin": 1,
    }


def _guion_admin(materias, *, porcentajes=(), tipos=(), celdas=()):
    return [
        ("AS promedio_numerico", None, materias),
        ("as director_grupo_nombre", {"estudiante_nombre": "Sara", "estudiante_apellido": "López",
                                      "curso_nombre": "Quinto"}, []),
        ("RANK() OVER", {"puesto": 1, "total": 30}, []),
        (PORCENTAJES_VARIAS, None, porcentajes),
        (TIPOS_VARIAS, None, tipos),
        (CELDAS_DEL_ESTUDIANTE, None, celdas),
    ]


def _definitivas(respuesta):
    return {m["materia"]: m["definitiva"] for m in respuesta["materias"]}


def test_el_boletin_del_admin_con_todo_guardado_no_pregunta_por_porcentajes(boletin):
    cursor = boletin(_guion_admin([_materia(44, "Historia", Decimal("3.50"), boletin_id=900)]))

    respuesta = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert _definitivas(respuesta) == {"Historia": 3.5}
    assert cursor.leyo(PORCENTAJES_VARIAS) == []


def test_el_boletin_del_admin_sin_porcentajes_da_el_promedio_de_hoy(boletin):
    cursor = boletin(_guion_admin([_materia(44, "Historia", Decimal("4.00"))]))

    respuesta = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert _definitivas(respuesta) == {"Historia": 4.0}
    assert cursor.leyo(PORCENTAJES_VARIAS) == [([44], 2)]
    assert cursor.leyo(CELDAS_DEL_ESTUDIANTE) == []


def test_el_boletin_del_admin_con_porcentajes_activos_usa_la_nota_ponderada(boletin):
    """Historia no tiene boletin guardado: el respaldo era el promedio simple
    (4.00) y pasa a ser el ponderado (3.90). Arte si lo tiene guardado y no
    cambia aunque su clase tambien tenga porcentajes."""
    cursor = boletin(_guion_admin(
        [_materia(44, "Historia", Decimal("4.00")),
         _materia(45, "Arte", Decimal("3.50"), boletin_id=900)],
        porcentajes=_porcentajes(44),
        tipos=_tipos(44),
        celdas=[(44, "Cognitivo", Decimal("4.00"), None),
                (44, "Procedimental", Decimal("3.00"), None),
                (44, "Actitudinal", Decimal("5.00"), None)],
    ))

    respuesta = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert _definitivas(respuesta) == {"Historia": 3.9, "Arte": 3.5}
    # Solo se pregunta por la clase sin boletin guardado.
    assert cursor.leyo(PORCENTAJES_VARIAS) == [([44], 2)]
    assert cursor.leyo(CELDAS_DEL_ESTUDIANTE) == [([44], 2, 8)]


def test_el_boletin_del_admin_con_porcentajes_incompletos_da_el_de_hoy(boletin):
    cursor = boletin(_guion_admin(
        [_materia(44, "Historia", Decimal("4.00"))],
        porcentajes=[(44, "Cognitivo", 50)],
        tipos=_tipos(44),
    ))

    respuesta = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert _definitivas(respuesta) == {"Historia": 4.0}
    assert cursor.leyo(CELDAS_DEL_ESTUDIANTE) == []


def test_el_boletin_del_admin_no_pondera_caritas(boletin):
    """Preescolar: el respaldo de hoy deja vacia la nota y asi sigue."""
    cursor = boletin(_guion_admin(
        [_materia(44, "Dimensión cognitiva", None)],
        porcentajes=_porcentajes(44),
        tipos=_tipos(44),
        celdas=[(44, "Cognitivo", None, "destacado"), (44, "Procedimental", None, "logrado")],
    ))

    respuesta = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert _definitivas(respuesta) == {"Dimensión cognitiva": None}
    assert cursor.leyo(CELDAS_DEL_ESTUDIANTE) == [([44], 2, 8)]


# --------------------------------------------------------------------------
# Reporte parcial
# --------------------------------------------------------------------------

def _celda(asignacion_id, materia, celda_id, descripcion, nota, tipo="numerica", valoracion=None):
    return {
        "asignacion_id": asignacion_id, "materia_id": asignacion_id + 100, "materia": materia,
        "profesor_nombre": "Ana", "profesor_apellido": "Ruiz", "orden_boletin": 1,
        "nota_detalle_id": celda_id, "descripcion": descripcion, "nota": nota,
        "tipo_evaluacion": tipo, "valoracion": valoracion,
    }


def _guion_reporte(celdas, *, porcentajes=(), tipos=()):
    return [
        ("AS director_grupo_nombre", {"estudiante_nombre": "Sara", "estudiante_apellido": "López",
                                      "curso_nombre": "Quinto"}, []),
        ("AS nota_detalle_id", None, celdas),
        (PORCENTAJES_VARIAS, None, porcentajes),
        (TIPOS_VARIAS, None, tipos),
    ]


CELDAS_DEL_REPORTE = [
    _celda(44, "Historia", 101, "Cognitivo", Decimal("4.00")),
    _celda(44, "Historia", 102, "Procedimental", Decimal("3.00")),
    _celda(44, "Historia", 103, "Actitudinal", Decimal("5.00")),
    _celda(44, "Historia", 104, "mas_alto", Decimal("1.00")),
    _celda(45, "Arte", 105, "Cognitivo", Decimal("3.00")),
]


def test_el_reporte_parcial_sin_porcentajes_da_el_promedio_de_hoy(boletin):
    cursor = boletin(_guion_reporte(CELDAS_DEL_REPORTE))

    respuesta = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    historia, arte = respuesta["materias"]
    # (4 + 3 + 5 + 1) / 4, con la columna interna, sin redondear: lo de hoy.
    assert historia["definitiva"] == 3.25
    assert arte["definitiva"] == 3.0
    assert cursor.leyo(PORCENTAJES_VARIAS) == [([44, 45], 2)]


def test_el_reporte_parcial_con_porcentajes_activos_usa_la_nota_ponderada(boletin):
    """Con porcentajes, `mas_alto` no cuenta (no lleva porcentaje). Arte no
    tiene porcentajes y sigue con su promedio de hoy."""
    cursor = boletin(_guion_reporte(
        CELDAS_DEL_REPORTE, porcentajes=_porcentajes(44), tipos=_tipos(44) + [(44, "mas_alto")],
    ))

    respuesta = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    historia, arte = respuesta["materias"]
    assert historia["definitiva"] == 3.9
    assert arte["definitiva"] == 3.0
    # Los detalles no cambian: siguen siendo todas las celdas.
    assert len(historia["detalles"]) == 4
    # Las celdas ya venian en la lectura del reporte: no se piden otra vez.
    assert cursor.leyo(CELDAS_DEL_ESTUDIANTE) == []


def test_el_reporte_parcial_sin_materias_no_pregunta_por_porcentajes(boletin):
    cursor = boletin(_guion_reporte([]))

    boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    assert cursor.leyo(PORCENTAJES_VARIAS) == []


def test_el_reporte_parcial_no_pondera_caritas(boletin):
    caritas = [
        _celda(44, "Dimensión", 101, "Cognitivo", None, "desarrollo", "destacado"),
        _celda(44, "Dimensión", 102, "Procedimental", None, "desarrollo", "logrado"),
    ]
    boletin(_guion_reporte(caritas, porcentajes=_porcentajes(44), tipos=_tipos(44)))

    respuesta = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    assert respuesta["materias"][0]["definitiva"] is None


# --------------------------------------------------------------------------
# Rankings de una clase y un periodo
# --------------------------------------------------------------------------

def _celdas_clase(estudiante_id, nombre, **notas):
    return [(estudiante_id, nombre, tipo, nota, None) for tipo, nota in notas.items()]


CELDAS_DE_LA_CLASE_ACTIVA = (
    _celdas_clase(1, "Ana Ríos", Cognitivo=Decimal("2.00"), Procedimental=Decimal("3.00"),
                  Actitudinal=Decimal("3.00"))
    # 2.995 truncado seria 2.99 (bajo); mitad hacia arriba es 3.00 (no bajo).
    + _celdas_clase(2, "Beto Paz", Cognitivo=Decimal("3.00"), Procedimental=Decimal("2.99"),
                    Actitudinal=Decimal("2.99"))
    + _celdas_clase(3, "Luis Gil", Cognitivo=Decimal("4.00"), Procedimental=Decimal("3.00"),
                    Actitudinal=Decimal("5.00"))
    + [(4, "Eva Soto", "Cognitivo", None, "destacado")]
)
CLASE_ACTIVA = [
    (PORCENTAJES_UNA, None, list(PESOS.items())),
    (TIPOS_UNA, None, [(tipo,) for tipo in PESOS]),
    (CELDAS_DE_LA_CLASE, None, CELDAS_DE_LA_CLASE_ACTIVA),
]


def test_el_ranking_sin_porcentajes_usa_la_consulta_de_hoy(tablero):
    cursor = tablero([
        (PORCENTAJES_UNA, None, []),
        (RANKING_DE_HOY, None, [(11, "Ana Ríos", Decimal("2.40"))]),
    ])

    resultado = dashboard_controller.obtener_ranking_rendimiento_controller(12, 2)

    assert resultado == [{"id": 11, "nombre": "Ana Ríos", "promedio": 2.4}]
    assert cursor.leyo(PORCENTAJES_UNA) == [(77, 2)]
    assert cursor.leyo(CELDAS_DE_LA_CLASE) == []


def test_el_ranking_bajo_con_porcentajes_activos_usa_la_nota_ponderada(tablero):
    cursor = tablero(CLASE_ACTIVA)

    resultado = dashboard_controller.obtener_ranking_rendimiento_controller(12, 2)

    # Ana: 2.0 x 50 % + 3.0 x 30 % + 3.0 x 20 % = 2.50. Beto redondea a 3.00 y
    # sale de la lista. Eva solo tiene caritas: no entra en los rankings.
    assert resultado == [{"id": 1, "nombre": "Ana Ríos", "promedio": 2.5}]
    assert cursor.leyo(RANKING_DE_HOY) == []
    assert cursor.leyo(CELDAS_DE_LA_CLASE) == [(77, 2)]


def test_el_ranking_mejor_con_porcentajes_activos_ordena_de_mayor_a_menor(tablero):
    tablero(CLASE_ACTIVA)

    resultado = dashboard_controller.obtener_ranking_mejor_rendimiento_controller(12, 2)

    assert resultado == [
        {"id": 3, "nombre": "Luis Gil", "promedio": 3.9},
        {"id": 2, "nombre": "Beto Paz", "promedio": 3.0},
    ]


def test_el_ranking_con_porcentajes_incompletos_usa_la_consulta_de_hoy(tablero):
    cursor = tablero([
        (PORCENTAJES_UNA, None, [("Cognitivo", 50)]),
        (TIPOS_UNA, None, [(tipo,) for tipo in PESOS]),
        (RANKING_DE_HOY, None, []),
    ])

    dashboard_controller.obtener_ranking_mejor_rendimiento_controller(12, 2)

    assert len(cursor.leyo(RANKING_DE_HOY)) == 1
    assert cursor.leyo(CELDAS_DE_LA_CLASE) == []
