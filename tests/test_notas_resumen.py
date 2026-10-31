"""Notas por periodo en el resumen del estudiante: el calculo y sus lecturas.

Ver `docs/funcionalidades/NOTAS_RESUMEN_ESTUDIANTE.md`. El calculo es puro
(`app/core/notas_resumen.py`). Las consultas del controlador las fija
`test_asignaciones_estudiantes_caracterizacion.py`, y las del año
`test_anio_lectivo_lecturas.py`.
"""
from decimal import Decimal

import pytest

from app.core.notas_resumen import (
    armar_notas_por_periodo,
    inasistencias_por_periodo,
    nota_del_anio,
    nota_del_periodo,
    nota_sin_porcentajes,
    notas_compatibles,
    notas_por_periodo_vacias,
)
from app.services import porcentajes_activos


def numerica(asignacion_id, materia, periodo, nota, tipo="Taller", nivel="primaria"):
    valor = None if nota is None else Decimal(str(nota))
    return (asignacion_id, materia, nivel, periodo, tipo, valor, "numerica", None)


def carita(asignacion_id, materia, periodo, valoracion, tipo="Juego", nivel="preescolar"):
    return (asignacion_id, materia, nivel, periodo, tipo, None, "desarrollo", valoracion)


# ---------------------------------------------------------------------------
# La nota de una materia en un periodo
# ---------------------------------------------------------------------------


def test_primaria_promedia_las_notas_de_1_a_5_sin_ceros():
    """Los ceros no cuentan, igual que el reporte parcial y el boletin."""
    celdas = [("Taller", Decimal("4.0"), None), ("Quiz", Decimal("0"), None), ("Examen", Decimal("3.0"), None)]

    assert nota_sin_porcentajes("numerica", celdas) == (Decimal("3.50"), None)


def test_las_columnas_internas_no_cuentan():
    """`mas_alto` y "Desde React" no se ven en la planilla y no promedian."""
    celdas = [
        ("Taller", Decimal("4.0"), None),
        ("mas_alto", Decimal("5.0"), None),
        ("Desde React", Decimal("1.0"), None),
    ]

    assert nota_sin_porcentajes("numerica", celdas) == (Decimal("4.00"), None)


def test_dos_decimales_mitad_hacia_arriba():
    celdas = [("A", Decimal("3.33"), None), ("B", Decimal("3.34"), None)]

    # 3,335 exacto sube a 3,34.
    assert nota_sin_porcentajes("numerica", celdas) == (Decimal("3.34"), None)


@pytest.mark.parametrize(
    "caritas, esperado",
    [
        (["logrado", "destacado"], (Decimal("4.50"), "destacado")),
        (["logrado", "logrado", "destacado"], (Decimal("4.33"), "logrado")),
        (["apoyo", "proceso"], (Decimal("2.50"), "proceso")),
        (["", None, "otra"], (None, None)),
    ],
)
def test_preescolar_pasa_las_caritas_a_numero_y_vuelve_a_la_mas_cercana(caritas, esperado):
    """La misma escala y el mismo desempate que la planilla (P8)."""
    celdas = [(f"T{indice}", None, valoracion) for indice, valoracion in enumerate(caritas)]

    assert nota_sin_porcentajes("desarrollo", celdas) == esperado


def test_con_porcentajes_activos_es_la_ponderada():
    celdas = [("Cognitivo", Decimal("5.0"), None), ("Actitudinal", Decimal("3.0"), None)]

    assert nota_del_periodo("numerica", celdas) == (Decimal("4.00"), None)
    assert nota_del_periodo(
        "numerica", celdas, {"Cognitivo": 75, "Actitudinal": 25}
    ) == (Decimal("4.50"), None)


def test_sin_celdas_no_hay_nota():
    assert nota_del_periodo("numerica", []) == (None, None)
    assert nota_del_periodo("desarrollo", []) == (None, None)


# ---------------------------------------------------------------------------
# "Todo el año"
# ---------------------------------------------------------------------------


def test_el_anio_es_el_promedio_de_los_periodos_con_nota():
    assert nota_del_anio("numerica", [Decimal("4.00"), None, Decimal("3.00"), None]) == (
        Decimal("3.50"),
        None,
    )
    assert nota_del_anio("desarrollo", [Decimal("4.00"), Decimal("5.00")]) == (
        Decimal("4.50"),
        "destacado",
    )
    assert nota_del_anio("numerica", [None, None]) == (None, None)


# ---------------------------------------------------------------------------
# La respuesta
# ---------------------------------------------------------------------------


def test_arma_las_materias_en_su_orden_con_los_cuatro_periodos_y_el_anio():
    filas = [
        numerica(10, "Matemáticas", 1, 4.0),
        numerica(10, "Matemáticas", 1, 5.0, tipo="Quiz"),
        numerica(10, "Matemáticas", 3, 3.0),
        numerica(11, "Lengua", None, None),
    ]

    resumen = armar_notas_por_periodo(filas)

    matematicas, lengua = resumen["materias"]
    assert matematicas == {
        "materia": "Matemáticas",
        "tipo_evaluacion": "numerica",
        "periodos": {
            "1": {"nota": 4.5, "valoracion": None},
            "2": None,
            "3": {"nota": 3.0, "valoracion": None},
            "4": None,
        },
        "anio": {"nota": 3.75, "valoracion": None},
    }
    # Una materia sin notas sale igual, sin nota en ningun periodo.
    assert lengua == {
        "materia": "Lengua",
        "tipo_evaluacion": "numerica",
        "periodos": {"1": None, "2": None, "3": None, "4": None},
        "anio": None,
    }
    assert resumen["promedio"] == {"1": 4.5, "2": None, "3": 3.0, "4": None, "anio": 3.75}


def test_el_promedio_general_solo_mira_las_materias_numericas():
    filas = [
        numerica(10, "Matemáticas", 1, 4.0, nivel=None),
        carita(20, "Arte", 1, "destacado", nivel=None),
    ]

    resumen = armar_notas_por_periodo(filas)

    assert [m["tipo_evaluacion"] for m in resumen["materias"]] == ["numerica", "desarrollo"]
    assert resumen["promedio"]["1"] == 4.0


def test_preescolar_no_tiene_promedio_general():
    resumen = armar_notas_por_periodo([carita(20, "Dimensión cognitiva", 2, "logrado")])

    assert resumen["materias"][0]["periodos"]["2"] == {"nota": 4.0, "valoracion": "logrado"}
    assert resumen["promedio"] == {"1": None, "2": None, "3": None, "4": None, "anio": None}


def test_el_nivel_del_curso_manda_sobre_las_celdas():
    """Un curso de preescolar evalua con caritas aunque una celda diga otra cosa."""
    filas = [(20, "Arte", "preescolar", 1, "Juego", None, "numerica", "logrado")]

    [materia] = armar_notas_por_periodo(filas)["materias"]

    assert materia["tipo_evaluacion"] == "desarrollo"
    assert materia["periodos"]["1"]["valoracion"] == "logrado"


def test_los_porcentajes_se_aplican_por_clase_y_periodo():
    filas = [
        numerica(10, "Matemáticas", 1, 5.0, tipo="Cognitivo"),
        numerica(10, "Matemáticas", 1, 3.0, tipo="Actitudinal"),
        numerica(10, "Matemáticas", 2, 5.0, tipo="Cognitivo"),
        numerica(10, "Matemáticas", 2, 3.0, tipo="Actitudinal"),
    ]
    porcentajes = {(10, 1): {"Cognitivo": 75, "Actitudinal": 25}}

    periodos = armar_notas_por_periodo(filas, porcentajes)["materias"][0]["periodos"]

    assert periodos["1"]["nota"] == 4.5  # ponderada
    assert periodos["2"]["nota"] == 4.0  # sin porcentajes en el periodo 2


def test_la_forma_vacia_trae_los_cuatro_periodos_y_el_anio():
    assert notas_por_periodo_vacias() == {
        "materias": [],
        "promedio": {"1": None, "2": None, "3": None, "4": None, "anio": None},
    }


# ---------------------------------------------------------------------------
# La forma vieja, para el frontend de hoy
# ---------------------------------------------------------------------------


def test_la_forma_vieja_son_las_materias_numericas_del_anio_a_un_decimal():
    resumen = armar_notas_por_periodo([
        numerica(10, "Matemáticas", 1, 3.75),
        numerica(11, "Lengua", 1, 3.25),
        carita(20, "Arte", 1, "logrado", nivel=None),
        numerica(12, "Inglés", None, None),
    ])

    notas, promedio = notas_compatibles(resumen)

    assert notas == [
        {"materia": "Matemáticas", "promedio": 3.8},
        {"materia": "Lengua", "promedio": 3.3},
    ]
    assert promedio == 3.5


def test_sin_materias_numericas_el_promedio_viejo_es_cero():
    assert notas_compatibles(notas_por_periodo_vacias()) == ([], 0.0)


# ---------------------------------------------------------------------------
# Inasistencias
# ---------------------------------------------------------------------------


def test_las_inasistencias_por_periodo_y_su_total():
    assert inasistencias_por_periodo((2, 0, 1, 0, 4)) == {"1": 2, "2": 0, "3": 1, "4": 0, "anio": 4}
    assert inasistencias_por_periodo(None) == {"1": 0, "2": 0, "3": 0, "4": 0, "anio": 0}


# ---------------------------------------------------------------------------
# Los porcentajes activos del año
# ---------------------------------------------------------------------------


class CursorDePorcentajes:
    def __init__(self, porcentajes=(), tipos=()):
        self.consultas = []
        self._respuestas = {"planilla_tipos_porcentaje": list(porcentajes), "notas_detalle": list(tipos)}
        self._filas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(sql.split()), params))
        tabla = "planilla_tipos_porcentaje" if "planilla_tipos_porcentaje" in sql else "notas_detalle"
        self._filas = self._respuestas[tabla]

    def fetchall(self):
        return list(self._filas)


def test_sin_clases_no_consulta_nada():
    cursor = CursorDePorcentajes()

    assert porcentajes_activos.porcentajes_activos_del_anio(cursor, []) == {}
    assert cursor.consultas == []


def test_sin_porcentajes_es_una_sola_consulta_para_todo_el_anio():
    cursor = CursorDePorcentajes()

    assert porcentajes_activos.porcentajes_activos_del_anio(cursor, [10, 11]) == {}
    [(sql, params)] = cursor.consultas
    assert "WHERE asignacion_id = ANY(%s)" in sql
    assert "periodo =" not in sql
    assert params == ([10, 11],)


def test_solo_cuentan_las_clases_y_periodos_que_suman_100():
    cursor = CursorDePorcentajes(
        porcentajes=[
            (10, 1, "Cognitivo", 60), (10, 1, "Actitudinal", 40),
            (10, 2, "Cognitivo", 60),
        ],
        tipos=[
            (10, 1, "Cognitivo"), (10, 1, "Actitudinal"),
            (10, 2, "Cognitivo"), (10, 2, "Actitudinal"),
        ],
    )

    activos = porcentajes_activos.porcentajes_activos_del_anio(cursor, [10])

    assert activos == {(10, 1): {"Cognitivo": 60, "Actitudinal": 40}}
    assert len(cursor.consultas) == 2
