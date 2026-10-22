"""La nota de un periodo con porcentajes por tipo de nota (parte B, paso B2a).

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`, "Propuestas de B0": PB2 a
PB4, QB1 y QB2. Son reglas puras: sin base de datos y sin HTTP.

El frontend tendra la gemela para la vista previa (paso B4) con estos mismos
casos. Si una regla cambia aqui, cambia alla.
"""

from decimal import Decimal

import pytest

from app.core.nota_periodo import (
    PORCENTAJE_MAXIMO,
    PORCENTAJE_MINIMO,
    SUMA_COMPLETA,
    admite_porcentaje,
    calcular_nota_del_periodo,
    es_porcentaje_valido,
    porcentajes_activos,
    suma_de_porcentajes,
)


TIPOS = ["Cognitivo", "Procedimental", "Actitudinal"]
COMPLETOS = {"Cognitivo": 50, "Procedimental": 30, "Actitudinal": 20}


def _numericas(**notas):
    return [(tipo, nota, None) for tipo, nota in notas.items()]


def _caritas(**codigos):
    return [(tipo, None, codigo) for tipo, codigo in codigos.items()]


# --------------------------------------------------------------------------
# PB2: porcentajes enteros de 1 a 100
# --------------------------------------------------------------------------

def test_los_limites_son_enteros_de_1_a_100_y_la_suma_completa_es_100():
    assert (PORCENTAJE_MINIMO, PORCENTAJE_MAXIMO, SUMA_COMPLETA) == (1, 100, 100)


@pytest.mark.parametrize("valor", [1, 33, 34, 100])
def test_acepta_enteros_de_1_a_100(valor):
    assert es_porcentaje_valido(valor) is True


@pytest.mark.parametrize(
    "valor",
    [0, 101, -5, 33.5, 33.0, "40", None, True, Decimal("40")],
    ids=["cero", "mas-de-100", "negativo", "decimal", "flotante-entero", "texto",
         "vacio", "booleano", "decimal-exacto"],
)
def test_rechaza_lo_que_no_es_un_entero_de_1_a_100(valor):
    assert es_porcentaje_valido(valor) is False


@pytest.mark.parametrize("tipo", ["mas_alto", " MAS_ALTO ", "Desde React", "desde react"])
def test_las_columnas_internas_no_llevan_porcentaje(tipo):
    assert admite_porcentaje(tipo) is False


def test_un_tipo_de_nota_normal_si_lleva_porcentaje():
    assert admite_porcentaje("Cognitivo") is True


# --------------------------------------------------------------------------
# QB2: todo o nada
# --------------------------------------------------------------------------

def test_activos_cuando_todos_los_tipos_tienen_porcentaje_y_suman_100():
    assert porcentajes_activos(TIPOS, COMPLETOS) is True


def test_no_activos_si_falta_el_porcentaje_de_un_tipo():
    faltante = {"Cognitivo": 50, "Procedimental": 50}
    assert porcentajes_activos(TIPOS, faltante) is False


def test_no_activos_si_suman_menos_de_100():
    assert porcentajes_activos(TIPOS, {**COMPLETOS, "Actitudinal": 10}) is False


def test_no_activos_sin_ningun_porcentaje():
    assert porcentajes_activos(TIPOS, {}) is False


def test_no_activos_sin_tipos_de_nota():
    assert porcentajes_activos([], {"Cognitivo": 100}) is False


def test_las_columnas_internas_no_cuentan_para_estar_completos():
    assert porcentajes_activos(TIPOS + ["mas_alto", "Desde React"], COMPLETOS) is True


def test_el_porcentaje_de_un_tipo_que_ya_no_existe_no_cuenta():
    sobrante = {"Cognitivo": 70, "Procedimental": 30, "Borrado": 40}
    assert porcentajes_activos(["Cognitivo", "Procedimental"], sobrante) is True
    assert suma_de_porcentajes(["Cognitivo", "Procedimental"], sobrante) == 100


def test_los_tipos_se_comparan_sin_mayusculas_ni_espacios_en_los_extremos():
    """Igual que `LOWER(TRIM(...))` en SQL y que las subnotas."""
    guardados = {" cognitivo ": 50, "PROCEDIMENTAL": 30, "actitudinal": 20}
    assert porcentajes_activos(TIPOS, guardados) is True
    assert suma_de_porcentajes(TIPOS, guardados) == 100


def test_la_suma_solo_mira_los_tipos_de_la_planilla():
    assert suma_de_porcentajes(TIPOS, {"Cognitivo": 40, "Procedimental": 30}) == 70
    assert suma_de_porcentajes(TIPOS, {}) == 0


# --------------------------------------------------------------------------
# PB4: la nota ponderada (primaria)
# --------------------------------------------------------------------------

def test_ejemplo_de_b0_con_las_tres_notas():
    """4.0 x 50 % + 3.0 x 30 % + 5.0 x 20 % = 2.0 + 0.9 + 1.0 = 3.90."""
    celdas = _numericas(Cognitivo=4.0, Procedimental=3.0, Actitudinal=5.0)

    assert calcular_nota_del_periodo("numerica", celdas, COMPLETOS) == (Decimal("3.90"), None)


def test_ejemplo_de_b0_sin_una_nota_reparte_su_peso():
    """(2.0 + 0.9) / 0.8 = 3.625, mitad hacia arriba: 3.63 (Python daria 3.62)."""
    celdas = _numericas(Cognitivo=4.0, Procedimental=3.0, Actitudinal=None)

    assert calcular_nota_del_periodo("numerica", celdas, COMPLETOS) == (Decimal("3.63"), None)


def test_con_una_sola_nota_el_resultado_es_esa_nota():
    celdas = _numericas(Cognitivo=None, Procedimental=3.7, Actitudinal=None)

    assert calcular_nota_del_periodo("numerica", celdas, COMPLETOS) == (Decimal("3.70"), None)


def test_sin_ninguna_nota_queda_vacia():
    celdas = _numericas(Cognitivo=None, Procedimental=None, Actitudinal=None)

    assert calcular_nota_del_periodo("numerica", celdas, COMPLETOS) == (None, None)
    assert calcular_nota_del_periodo("numerica", [], COMPLETOS) == (None, None)


@pytest.mark.parametrize(
    ("primera", "segunda", "esperada"),
    [
        (4.10, 4.15, Decimal("4.13")),
        (1.00, 1.01, Decimal("1.01")),
        (Decimal("3.25"), Decimal("4.00"), Decimal("3.63")),
    ],
    ids=["4.125", "1.005-en-flotante-saldria-1.00", "3.625-desde-la-base"],
)
def test_redondea_a_dos_decimales_mitad_hacia_arriba(primera, segunda, esperada):
    mitad = {"Cognitivo": 50, "Procedimental": 50}
    celdas = _numericas(Cognitivo=primera, Procedimental=segunda)

    assert calcular_nota_del_periodo("numerica", celdas, mitad) == (esperada, None)


def test_tres_tipos_iguales_con_33_33_34():
    """PB2: sin decimales, tres tipos iguales son 33 + 33 + 34."""
    tercios = {"Cognitivo": 33, "Procedimental": 33, "Actitudinal": 34}
    celdas = _numericas(Cognitivo=5.0, Procedimental=4.0, Actitudinal=3.0)

    # (5 x 33 + 4 x 33 + 3 x 34) / 100 = 3.99
    assert calcular_nota_del_periodo("numerica", celdas, tercios) == (Decimal("3.99"), None)


def test_las_columnas_internas_no_cuentan_en_la_nota():
    celdas = _numericas(Cognitivo=4.0, Procedimental=3.0, Actitudinal=5.0)
    celdas.append(("mas_alto", 1.0, None))

    assert calcular_nota_del_periodo("numerica", celdas, COMPLETOS) == (Decimal("3.90"), None)


def test_una_nota_fuera_de_1_a_5_no_cuenta():
    """Datos viejos: un cero no cuenta, igual que en el boletin y el reporte
    parcial de hoy, que descartan `nota > 0`."""
    celdas = _numericas(Cognitivo=4.0, Procedimental=0, Actitudinal=None)

    assert calcular_nota_del_periodo("numerica", celdas, COMPLETOS) == (Decimal("4.00"), None)


def test_los_tipos_de_las_celdas_tambien_se_comparan_sin_mayusculas():
    celdas = [(" cognitivo", 4.0, None), ("PROCEDIMENTAL ", 3.0, None), ("Actitudinal", 5.0, None)]

    assert calcular_nota_del_periodo("numerica", celdas, COMPLETOS) == (Decimal("3.90"), None)


def test_una_celda_sin_porcentaje_no_cuenta():
    """Con porcentajes activos no deberia pasar; si pasa, esa celda no pesa."""
    celdas = _numericas(Cognitivo=4.0, Procedimental=3.0, Actitudinal=5.0)
    celdas.append(("Otro", 1.0, None))

    assert calcular_nota_del_periodo("numerica", celdas, COMPLETOS) == (Decimal("3.90"), None)


# --------------------------------------------------------------------------
# QB1: preescolar, con caritas
# --------------------------------------------------------------------------

def test_caritas_con_empate_gana_la_mas_alta():
    """50 % destacado (5) y 50 % logrado (4): 4.5, empate, destacado."""
    mitad = {"Cognitivo": 50, "Procedimental": 50}
    celdas = _caritas(Cognitivo="destacado", Procedimental="logrado")

    assert calcular_nota_del_periodo("desarrollo", celdas, mitad) == (Decimal("4.50"), "destacado")


def test_caritas_sin_empate_va_a_la_mas_cercana():
    """60 % logrado (4) y 40 % proceso (3): 3.6, mas cerca de logrado."""
    pesos = {"Cognitivo": 60, "Procedimental": 40}
    celdas = _caritas(Cognitivo="logrado", Procedimental="proceso")

    assert calcular_nota_del_periodo("desarrollo", celdas, pesos) == (Decimal("3.60"), "logrado")


def test_caritas_reparten_el_peso_de_la_que_falta():
    celdas = _caritas(Cognitivo="apoyo", Procedimental=None, Actitudinal="destacado")

    # (2 x 50 + 5 x 20) / 70 = 2.857..., mas cerca de proceso (3)
    assert calcular_nota_del_periodo("desarrollo", celdas, COMPLETOS) == (Decimal("2.86"), "proceso")


def test_casi_empate_no_es_empate():
    """49 % destacado y 50 % logrado (el tercer tipo sin carita): 445 / 99 =
    4.4949..., mas cerca de logrado. Con porcentajes enteros que suman hasta
    100, el promedio nunca cae entre 4.495 y 4.5, asi que redondear antes o
    despues no cambia la carita; el modulo usa el promedio exacto igual."""
    pesos = {"Cognitivo": 49, "Procedimental": 50, "Actitudinal": 1}
    celdas = _caritas(Cognitivo="destacado", Procedimental="logrado", Actitudinal=None)

    assert calcular_nota_del_periodo("desarrollo", celdas, pesos) == (Decimal("4.49"), "logrado")


def test_una_carita_que_no_es_de_la_escala_no_cuenta():
    celdas = _caritas(Cognitivo="logrado", Procedimental="inventada", Actitudinal=None)

    assert calcular_nota_del_periodo("desarrollo", celdas, COMPLETOS) == (Decimal("4.00"), "logrado")


def test_sin_ninguna_carita_queda_vacia():
    celdas = _caritas(Cognitivo=None, Procedimental=None, Actitudinal=None)

    assert calcular_nota_del_periodo("desarrollo", celdas, COMPLETOS) == (None, None)
