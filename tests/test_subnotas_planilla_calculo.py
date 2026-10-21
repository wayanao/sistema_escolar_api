"""Subnotas de la planilla, paso A1: el calculo de la celda, sin base de datos.

Reglas P2, P7 y P8 de `docs/funcionalidades/SUBNOTAS_PLANILLA.md`. El frontend
repite la misma formula para la vista previa del modal; estos casos son los que
las dos copias deben dar igual.
"""

from decimal import Decimal

import pytest

from app.core.subnotas_planilla import (
    admite_subnotas,
    armar_subnotas_de_planilla,
    calcular_celda,
    normalizar_nota,
    promedio_de_notas,
    promedio_de_valoraciones,
    tipo_de_calificaciones,
)
from app.core.valoraciones_desarrollo import (
    VALORACIONES_DESARROLLO,
    valoracion_desde_promedio,
)


# ---------------------------------------------------------------------------
# La escala de caritas
# ---------------------------------------------------------------------------


def test_la_escala_es_la_misma_del_frontend():
    """Prueba gemela de la del frontend (`valoracionesDesarrollo.test.js`). Si
    falla, la escala cambio en un repo y no en el otro."""
    assert VALORACIONES_DESARROLLO == (
        ("destacado", 5),
        ("logrado", 4),
        ("proceso", 3),
        ("apoyo", 2),
    )


@pytest.mark.parametrize(
    "promedio,carita",
    [
        (5, "destacado"),
        (4.5, "destacado"),  # empate: gana la mas alta
        (4.33, "logrado"),
        (3.5, "logrado"),
        (2.5, "proceso"),
        (2, "apoyo"),
        (None, None),
    ],
)
def test_la_carita_de_un_promedio_es_la_mas_cercana(promedio, carita):
    assert valoracion_desde_promedio(promedio) == carita


# ---------------------------------------------------------------------------
# Notas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "valor,esperado",
    [
        (4, Decimal("4.00")),
        (4.5, Decimal("4.50")),
        (4.155, Decimal("4.16")),  # mitad hacia arriba, no al par
        (Decimal("3.80"), Decimal("3.80")),
        (1, Decimal("1.00")),
        (5, Decimal("5.00")),
    ],
)
def test_normalizar_nota_deja_dos_decimales(valor, esperado):
    assert normalizar_nota(valor) == esperado


@pytest.mark.parametrize(
    "valor",
    [0.99, 5.01, "4", True, None, float("nan"), float("inf"), [4]],
)
def test_normalizar_nota_rechaza_lo_que_no_es_una_nota(valor):
    assert normalizar_nota(valor) is None


@pytest.mark.parametrize(
    "notas,esperado",
    [
        ([4.0, 3.0, 4.4], Decimal("3.80")),  # el ejemplo del documento
        ([4.10, 4.15], Decimal("4.13")),  # 4.125: round() de Python daria 4.12
        ([1.0, 1.01], Decimal("1.01")),  # 1.005: en flotante saldria 1.00
        ([5.0], Decimal("5.00")),
        ([3.0, 4.0, 4.0], Decimal("3.67")),
        ([Decimal("4.00"), 3.5], Decimal("3.75")),
    ],
)
def test_promedio_de_notas_redondea_mitad_hacia_arriba(notas, esperado):
    assert promedio_de_notas(notas) == esperado


def test_promedio_sin_notas_es_vacio():
    assert promedio_de_notas([]) is None


def test_promedio_de_caritas():
    assert promedio_de_valoraciones(["destacado", "logrado"]) == "destacado"
    assert promedio_de_valoraciones(["logrado", "logrado", "destacado"]) == "logrado"
    assert promedio_de_valoraciones(["apoyo", "proceso"]) == "proceso"
    # Un codigo fuera de la escala no cuenta, como en el frontend.
    assert promedio_de_valoraciones(["Alto", "logrado"]) == "logrado"
    assert promedio_de_valoraciones(["Alto"]) is None
    assert promedio_de_valoraciones([]) is None


# ---------------------------------------------------------------------------
# La celda
# ---------------------------------------------------------------------------


def test_celda_numerica_ignora_las_subnotas_vacias():
    """P2: (5.0 + 3.5) / 2, el vacio no cuenta como cero ni como uno."""
    calificaciones = [(5.0, None), (None, None), (3.5, None)]

    assert calcular_celda("numerica", calificaciones) == (Decimal("4.25"), None)


def test_celda_sin_calificaciones_queda_vacia():
    """P4: sin nada calificado la celda queda vacia, para escribirla a mano."""
    assert calcular_celda("numerica", []) == (None, None)
    assert calcular_celda("desarrollo", [(None, None)]) == (None, None)


def test_celda_de_desarrollo_guarda_la_carita_sin_nota():
    """P8: igual que hoy, la celda de preescolar lleva la carita y nota vacia."""
    calificaciones = [(None, "destacado"), (None, "logrado")]

    assert calcular_celda("desarrollo", calificaciones) == (None, "destacado")


def test_cada_celda_usa_solo_las_calificaciones_de_su_tipo():
    """Un curso sin nivel puede tener de los dos tipos si el profesor cambio el
    selector: la celda numerica no promedia caritas, ni al reves."""
    mezcla = [(4.0, None), (None, "apoyo")]

    assert calcular_celda("numerica", mezcla) == (Decimal("4.00"), None)
    assert calcular_celda("desarrollo", mezcla) == (None, "apoyo")


def test_tipo_de_calificaciones():
    assert tipo_de_calificaciones([(None, "logrado")]) == "desarrollo"
    assert tipo_de_calificaciones([(4.0, None)]) == "numerica"
    assert tipo_de_calificaciones([(4.0, None), (None, "logrado")]) == "numerica"
    assert tipo_de_calificaciones([]) == "numerica"


@pytest.mark.parametrize("tipo", ["mas_alto", " MAS_ALTO ", "Desde React", "desde react"])
def test_las_columnas_internas_no_admiten_subnotas(tipo):
    assert not admite_subnotas(tipo)


def test_un_tipo_visible_si_admite_subnotas():
    assert admite_subnotas("Cognitivo")


# ---------------------------------------------------------------------------
# Las subnotas en la respuesta de la planilla
# ---------------------------------------------------------------------------


def test_armar_subnotas_usa_el_nombre_de_la_columna_y_claves_de_texto():
    filas = [
        (7, "cognitivo ", "Taller 1", 1, Decimal("4.00"), None),
        (7, "cognitivo ", "Taller 1", 2, Decimal("3.50"), None),
        (8, "Cognitivo", "Quiz", None, None, None),  # nadie la ha calificado
        (9, "Actitudinal", "Convivencia", 1, None, "logrado"),
        (10, "Borrado", "Huérfana", 1, Decimal("5.00"), None),  # no es columna
    ]

    por_tipo, por_estudiante = armar_subnotas_de_planilla(
        ["Cognitivo", "Actitudinal"], filas
    )

    assert por_tipo == {
        "Cognitivo": [{"id": 7, "nombre": "Taller 1"}, {"id": 8, "nombre": "Quiz"}],
        "Actitudinal": [{"id": 9, "nombre": "Convivencia"}],
    }
    assert por_estudiante == {
        1: {"7": 4.0, "9": "logrado"},
        2: {"7": 3.5},
    }
