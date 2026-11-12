"""Puntualidad de pagos (panel del admin, 2026-11-11).

Primero la regla, con cuentas puras (`app/services/puntualidad.py`); después el
armado completo con una base de mentiras, que además cuenta las consultas:
no crecen con los estudiantes.
"""
from contextlib import contextmanager
from datetime import date, datetime, timedelta

import pytest

from app.controllers import puntualidad_controller
from app.services.cartera import CuotaVencida
from app.services.puntualidad import (
    MEJORES_DEL_COLEGIO,
    MEJORES_POR_CURSO,
    Abono,
    armar_puntualidad,
    evaluar_cuotas,
    resumir_estudiante,
    solo_fecha,
)

# Día límite 5 y 3 días de gracia: la cuota de febrero vence el 5 y se puede
# pagar sin estar tarde hasta el 8.
DIA_LIMITE = 5
GRACIA = 3
VALOR = 100000


def cuota(mes, anio=2026):
    vencimiento = date(anio, mes, DIA_LIMITE)
    return CuotaVencida(
        periodo=date(anio, mes, 1),
        fecha_vencimiento=vencimiento,
        fecha_efectiva=vencimiento + timedelta(days=GRACIA),
    )


def pagada(dia):
    return Abono(VALOR, dia)


# --- La regla, cuota por cuota ----------------------------------------------


def test_pagar_antes_del_limite_es_a_tiempo():
    [febrero] = evaluar_cuotas([cuota(2)], VALOR, {}, [pagada(date(2026, 2, 1))])

    assert febrero.pagada
    assert febrero.a_tiempo
    assert febrero.dias_antes == 4


def test_pagar_en_los_dias_de_gracia_sigue_siendo_a_tiempo():
    [febrero] = evaluar_cuotas([cuota(2)], VALOR, {}, [pagada(date(2026, 2, 8))])

    assert febrero.a_tiempo
    assert febrero.dias_antes == -3


def test_pagar_despues_de_la_gracia_es_tarde():
    [febrero] = evaluar_cuotas([cuota(2)], VALOR, {}, [pagada(date(2026, 2, 9))])

    assert febrero.pagada
    assert not febrero.a_tiempo


def test_una_cuota_sin_pagar_no_esta_a_tiempo():
    [febrero] = evaluar_cuotas([cuota(2)], VALOR, {}, [])

    assert not febrero.pagada
    assert not febrero.a_tiempo
    assert febrero.dias_antes is None


def test_en_abonos_cuenta_el_dia_del_abono_que_la_completa():
    [a_tiempo] = evaluar_cuotas(
        [cuota(2)], VALOR, {}, [Abono(60000, date(2026, 1, 20)), Abono(40000, date(2026, 2, 7))]
    )
    [tarde] = evaluar_cuotas(
        [cuota(2)], VALOR, {}, [Abono(60000, date(2026, 1, 20)), Abono(40000, date(2026, 2, 10))]
    )

    assert a_tiempo.fecha_pagada == date(2026, 2, 7)
    assert a_tiempo.a_tiempo
    assert tarde.fecha_pagada == date(2026, 2, 10)
    assert not tarde.a_tiempo


def test_los_pagos_van_de_la_cuota_mas_vieja_a_la_mas_nueva_en_cualquier_orden():
    pagos = [Abono(2 * VALOR, date(2026, 1, 15)), Abono(VALOR, date(2026, 4, 20))]

    for orden in (pagos, list(reversed(pagos))):
        febrero, marzo, abril = evaluar_cuotas([cuota(2), cuota(3), cuota(4)], VALOR, {}, orden)

        assert febrero.fecha_pagada == date(2026, 1, 15)
        assert marzo.fecha_pagada == date(2026, 1, 15)
        assert abril.fecha_pagada == date(2026, 4, 20)
        assert [febrero.a_tiempo, marzo.a_tiempo, abril.a_tiempo] == [True, True, False]


def test_un_adelanto_paga_el_mes_al_que_se_aplico():
    adelantos = {date(2026, 3, 1): [pagada(date(2026, 1, 10))]}

    febrero, marzo = evaluar_cuotas([cuota(2), cuota(3)], VALOR, adelantos, [pagada(date(2026, 2, 20))])

    assert not febrero.a_tiempo
    assert marzo.fecha_pagada == date(2026, 1, 10)
    assert marzo.a_tiempo


def test_solo_fecha_toma_el_dia_y_sin_fecha_usa_el_respaldo():
    hoy = date(2026, 11, 11)

    assert solo_fecha(datetime(2026, 2, 3, 15, 30), hoy) == date(2026, 2, 3)
    assert solo_fecha(date(2026, 2, 3), hoy) == date(2026, 2, 3)
    assert solo_fecha(None, hoy) == hoy


# --- Un estudiante -------------------------------------------------------------


DATOS = {"estudiante_id": 1, "nombre": "Ana", "apellido": "Arias", "curso_id": 10, "curso_nombre": "QUINTO"}


def test_resume_cuantas_a_tiempo_y_cuantos_dias_antes_suele_pagar():
    evaluadas = evaluar_cuotas(
        [cuota(2), cuota(3), cuota(4)],
        VALOR,
        {},
        [pagada(date(2026, 2, 1)), pagada(date(2026, 3, 3)), pagada(date(2026, 4, 20))],
    )

    resumen = resumir_estudiante(DATOS, evaluadas)

    assert resumen == {
        **DATOS,
        "cuotas_vencidas": 3,
        "cuotas_a_tiempo": 2,
        "dias_antes_promedio": 3.0,
        "siempre_a_tiempo": False,
        "debe": False,
    }


def test_siempre_a_tiempo_solo_si_todas_y_debe_si_falta_alguna():
    al_dia = resumir_estudiante(DATOS, evaluar_cuotas([cuota(2)], VALOR, {}, [pagada(date(2026, 2, 1))]))
    debe = resumir_estudiante(DATOS, evaluar_cuotas([cuota(2), cuota(3)], VALOR, {}, [pagada(date(2026, 2, 1))]))

    assert al_dia["siempre_a_tiempo"] is True
    assert al_dia["debe"] is False
    assert debe["siempre_a_tiempo"] is False
    assert debe["debe"] is True


def test_sin_cuotas_vencidas_no_se_cuenta():
    assert resumir_estudiante(DATOS, []) is None


# --- El colegio y los cursos ---------------------------------------------------


def evaluado(estudiante_id, curso_id, vencidas, a_tiempo, dias=None, debe=False, apellido=None):
    return {
        "estudiante_id": estudiante_id,
        "nombre": f"Nombre {estudiante_id}",
        "apellido": apellido or f"Apellido {estudiante_id}",
        "curso_id": curso_id,
        "curso_nombre": f"Curso {curso_id}",
        "cuotas_vencidas": vencidas,
        "cuotas_a_tiempo": a_tiempo,
        "dias_antes_promedio": dias,
        "siempre_a_tiempo": vencidas == a_tiempo,
        "debe": debe,
    }


def test_cuenta_quien_paga_siempre_a_tiempo_y_ordena_los_cursos_por_porcentaje():
    estudiantes = [
        evaluado(1, 10, 10, 10, 3),
        evaluado(2, 10, 10, 10, 5),
        evaluado(3, 20, 10, 10, 2),
        evaluado(4, 20, 10, 9, 4),
        evaluado(5, 20, 10, 7, 1, debe=True),
    ]

    respuesta = armar_puntualidad(estudiantes, date(2026, 11, 11))

    assert respuesta["fecha_corte"] == "2026-11-11"
    assert respuesta["total_estudiantes"] == 5
    assert respuesta["siempre_a_tiempo"] == 3
    assert respuesta["porcentaje"] == 60.0
    assert [(curso["curso_id"], curso["porcentaje"]) for curso in respuesta["cursos"]] == [(10, 100.0), (20, 33.3)]
    assert respuesta["cursos"][1]["estudiantes"] == 3
    assert respuesta["cursos"][1]["siempre_a_tiempo"] == 1


def test_el_ranking_desempata_por_dias_antes_y_deja_fuera_a_quien_debe():
    estudiantes = [
        evaluado(1, 10, 10, 10, 3),
        evaluado(2, 10, 10, 10, 7),
        evaluado(3, 10, 10, 9, 9),
        evaluado(4, 10, 10, 8, 30, debe=True),
    ]

    [curso] = armar_puntualidad(estudiantes, date(2026, 11, 11))["cursos"]

    assert [item["estudiante_id"] for item in curso["mejores"]] == [2, 1, 3]
    assert "debe" not in curso["mejores"][0]


def test_quien_nunca_pago_a_tiempo_se_cuenta_pero_no_entra_al_ranking():
    # Visto en el Colegio Demo: todo pagado, pero tarde, salía de primero.
    estudiantes = [
        evaluado(1, 10, 19, 0),
        evaluado(2, 10, 10, 1, -4),
    ]

    respuesta = armar_puntualidad(estudiantes, date(2026, 11, 11))

    assert respuesta["total_estudiantes"] == 2
    assert respuesta["cursos"][0]["estudiantes"] == 2
    assert [item["estudiante_id"] for item in respuesta["mejores"]] == [2]
    assert [item["estudiante_id"] for item in respuesta["cursos"][0]["mejores"]] == [2]


def test_cuantos_mejores_se_muestran():
    estudiantes = [evaluado(numero, 10, 10, 10, numero) for numero in range(1, 9)]

    respuesta = armar_puntualidad(estudiantes, date(2026, 11, 11))

    assert len(respuesta["mejores"]) == MEJORES_DEL_COLEGIO
    assert len(respuesta["cursos"][0]["mejores"]) == MEJORES_POR_CURSO
    assert respuesta["mejores"][0]["estudiante_id"] == 8


def test_sin_estudiantes_responde_vacio():
    assert armar_puntualidad([], date(2026, 11, 11)) == {
        "fecha_corte": "2026-11-11",
        "total_estudiantes": 0,
        "siempre_a_tiempo": 0,
        "porcentaje": 0.0,
        "mejores": [],
        "cursos": [],
    }


# --- Con la base (de mentiras) -----------------------------------------------

COLUMNAS_TIPOS = [
    "id", "nombre", "valor", "tipo_cobro", "activo", "mes_inicial", "mes_final",
    "frecuencia_meses", "dia_limite_mes", "dias_gracia", "mora_tipo", "mora_valor",
]

# Mensualidad de febrero a noviembre, día límite 5 y 3 de gracia. La
# matrícula no es mensual y el transporte está inactivo: no cuentan.
CONCEPTOS = [
    (1, "Mensualidad", 100000, "mensual", True, 2, 11, 1, 5, 3, None, 0, 2026),
    (2, "Matrícula", 300000, "unico", True, None, 12, 1, None, 0, None, 0, 2026),
    (3, "Transporte", 50000, "mensual", False, 2, 11, 1, 5, 3, None, 0, 2026),
]
# El curso 20 cobra la mensualidad más cara.
PRECIOS = [(10, 1, 100000), (10, 2, 300000), (20, 1, 120000)]

ESTUDIANTES = [
    (1, "Ana", "Arias", 10, "QUINTO"),
    (2, "Beto", "Bravo", 10, "QUINTO"),
    (3, "Carla", "Cruz", 20, "SEXTO"),
    (4, "Dani", "Díaz", 10, "QUINTO"),
]
# Dani está becado: su mensualidad vale 0.
VALORES = [(4, 1, 0)]

PAGOS = [
    # Ana paga con el concepto en la descripción, siempre antes del límite.
    (1, "efectivo", "mensualidad", 100000, datetime(2026, 2, 1, 9, 0)),
    (1, "efectivo", "mensualidad", 100000, datetime(2026, 3, 2, 9, 0)),
    (1, "efectivo", "matrícula", 300000, datetime(2026, 1, 20, 9, 0)),
    # Beto pagó febrero tarde (el 10) y marzo a tiempo.
    (2, "nequi", "mensualidad", 100000, datetime(2026, 2, 10, 9, 0)),
    (2, "nequi", "mensualidad", 100000, datetime(2026, 3, 1, 9, 0)),
    # Carla, un pago viejo con el concepto en `tipo_pago`.
    (3, "mensualidad", "pago de febrero", 120000, datetime(2026, 2, 4, 9, 0)),
]
# Carla adelantó marzo en enero.
ADELANTOS = [(3, 1, date(2026, 3, 1), 120000, datetime(2026, 1, 15, 9, 0))]


class CursorDePrueba:
    def __init__(self, estudiantes):
        self.estudiantes = estudiantes
        self.consultas = []
        self.filas = []

    def execute(self, consulta, params=None):
        texto = " ".join(str(consulta).lower().split())
        self.consultas.append(texto)
        self.filas = self._responder(texto)

    def _responder(self, texto):
        if "from information_schema.columns" in texto:
            return [(columna,) for columna in COLUMNAS_TIPOS]
        if "from information_schema.tables" in texto:
            return [(1,)]
        if "from tipos_de_pagos tp" in texto:
            return CONCEPTOS
        if "from tipos_pagos_cursos" in texto:
            return PRECIOS
        if "from estudiantes e" in texto and "join matriculas m" in texto:
            return self.estudiantes
        if "from tipos_pagos_estudiantes" in texto:
            return VALORES
        if "select pa.estudiante_id, pa.tipo_pago_id, pa.periodo" in texto:
            return ADELANTOS
        if "lower(coalesce(tipo_pago, ''))" in texto and "from pagos" in texto:
            # Solo pagos sin meses aplicados: el adelanto de Carla va aparte.
            assert "not exists" in texto
            return PAGOS
        raise AssertionError(f"Consulta no caracterizada: {texto}")

    def fetchall(self):
        return list(self.filas)

    def fetchone(self):
        return self.filas[0] if self.filas else None


@pytest.fixture
def base(monkeypatch):
    def preparar(estudiantes):
        cursor = CursorDePrueba(estudiantes)

        @contextmanager
        def falso_get_cursor(*args, **kwargs):
            yield cursor

        monkeypatch.setattr(puntualidad_controller, "get_cursor", falso_get_cursor)
        return cursor

    return preparar


# Marzo 20: ya vencieron febrero y marzo (hasta el 8 de cada mes), abril no.
HOY = date(2026, 3, 20)


def test_arma_la_puntualidad_del_colegio(base):
    base(ESTUDIANTES)

    respuesta = puntualidad_controller.reporte_puntualidad(hoy=HOY)

    # Dani (becado en $0) no se cuenta.
    assert respuesta["total_estudiantes"] == 3
    assert respuesta["siempre_a_tiempo"] == 2
    assert respuesta["porcentaje"] == 66.7
    # Carla suele pagar más días antes (adelantó marzo): va primero.
    assert [item["nombre"] for item in respuesta["mejores"]] == ["Carla", "Ana", "Beto"]
    ana = respuesta["mejores"][1]
    assert ana["cuotas_vencidas"] == 2
    assert ana["cuotas_a_tiempo"] == 2
    assert ana["dias_antes_promedio"] == 3.5
    beto = respuesta["mejores"][2]
    assert (beto["cuotas_a_tiempo"], beto["siempre_a_tiempo"]) == (1, False)

    [sexto, quinto] = respuesta["cursos"]
    assert (sexto["curso_nombre"], sexto["porcentaje"], sexto["estudiantes"]) == ("SEXTO", 100.0, 1)
    assert (quinto["curso_nombre"], quinto["porcentaje"], quinto["estudiantes"]) == ("QUINTO", 50.0, 2)
    assert [item["nombre"] for item in quinto["mejores"]] == ["Ana", "Beto"]


@pytest.mark.parametrize("cuantos", [1, 3, 4])
def test_las_consultas_no_crecen_con_los_estudiantes(base, cuantos):
    cursor = base(ESTUDIANTES[:cuantos])

    puntualidad_controller.reporte_puntualidad(hoy=HOY)

    # Conceptos (2), precios (2), estudiantes (1), valores personalizados (2),
    # ¿hay adelantos? (1), pagos (1) y adelantos (1).
    assert len(cursor.consultas) == 10


def test_sin_estudiantes_no_lee_pagos(base):
    cursor = base([])

    respuesta = puntualidad_controller.reporte_puntualidad(hoy=HOY)

    assert respuesta["total_estudiantes"] == 0
    assert len(cursor.consultas) == 5
    assert not any("from pagos" in consulta for consulta in cursor.consultas)
