"""Cobros y cartera calculan con la fecha de Colombia, no con la del servidor.

El 2026-09-30 a las 22:50 de Bogota (2026-10-01 03:50 UTC) produccion, que
corre en UTC, ya contaba vencida la cuota de octubre y el backend local no.
Estas pruebas fijan el reloj en ese instante y exigen el resultado de
Colombia. Ver app/core/fechas.py.
"""
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.core import fechas
from app.services import cobros
from app.services.cartera import calcular_cuotas_vencidas, calcular_deuda_concepto


RAIZ = Path(__file__).resolve().parents[1]

# 11 p. m. del 30 de septiembre en Bogota; ya 1 de octubre en UTC.
NOCHE_DEL_30 = datetime(2026, 10, 1, 4, 0, tzinfo=timezone.utc)

# Mensualidad de tenant_2005: julio a noviembre. Vencimiento el dia 1.
MENSUALIDAD = {
    "mes_inicial": 7,
    "mes_final": 11,
    "frecuencia_meses": 1,
    "dia_limite_mes": 1,
    "dias_gracia": 0,
}


@pytest.fixture
def reloj(monkeypatch):
    def fijar(instante):
        monkeypatch.setattr(fechas, "_ahora_utc", lambda: instante)

    return fijar


class CursorEspia:
    def __init__(self, una=None, todas=None):
        self.ejecutadas = []
        self._una = list(una or [])
        self._todas = list(todas or [])

    def execute(self, query, params=None):
        self.ejecutadas.append((query, params))

    def fetchone(self):
        return self._una.pop(0) if self._una else None

    def fetchall(self):
        return self._todas.pop(0) if self._todas else []


# ---------------------------------------------------------------------------
# La funcion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("instante_utc", "esperado"),
    [
        (NOCHE_DEL_30, date(2026, 9, 30)),
        # Medianoche en Bogota: ahi si cambia el dia.
        (datetime(2026, 10, 1, 5, 0, tzinfo=timezone.utc), date(2026, 10, 1)),
        # 31 de diciembre a las 11:30 p. m.: todavia no es 2027.
        (datetime(2027, 1, 1, 4, 30, tzinfo=timezone.utc), date(2026, 12, 31)),
    ],
)
def test_hoy_en_colombia_va_cinco_horas_detras_de_utc(reloj, instante_utc, esperado):
    reloj(instante_utc)

    assert fechas.hoy_en_colombia() == esperado


# ---------------------------------------------------------------------------
# El caso real del 2026-09-30
# ---------------------------------------------------------------------------


def test_la_noche_del_30_la_deuda_no_cuenta_todavia_octubre(reloj):
    reloj(NOCHE_DEL_30)

    deuda = calcular_deuda_concepto(
        valor_unitario=200000, tipo_cobro="mensual", pagado=0, max_cuotas=12,
        **MENSUALIDAD,
    )

    # Julio, agosto y septiembre. Con el reloj de Render daba 4.
    assert deuda["cuotas_vencidas"] == 3
    assert deuda["deuda"] == 600000


def test_la_proxima_cuota_de_la_noche_del_30_es_la_de_octubre(reloj):
    reloj(NOCHE_DEL_30)

    resultado = calcular_cuotas_vencidas(max_cuotas=12, **MENSUALIDAD)

    assert resultado.cuotas_vencidas == 3
    assert resultado.proxima_fecha == date(2026, 10, 1)


def test_a_medianoche_de_bogota_octubre_ya_vence(reloj):
    reloj(datetime(2026, 10, 1, 5, 0, tzinfo=timezone.utc))

    deuda = calcular_deuda_concepto(
        valor_unitario=200000, tipo_cobro="mensual", pagado=0, max_cuotas=12,
        **MENSUALIDAD,
    )

    assert deuda["cuotas_vencidas"] == 4


def test_meses_vencidos_la_noche_del_30_llegan_hasta_septiembre(reloj, monkeypatch):
    reloj(NOCHE_DEL_30)
    monkeypatch.setattr(
        cobros,
        "obtener_conceptos_mensuales_estudiante",
        lambda _cursor, _estudiante_id: [{
            "id": 2, "nombre": "Mensualidad", "valor_unitario": 200000.0,
            "valor_origen": "curso", **MENSUALIDAD,
        }],
    )
    monkeypatch.setattr(
        cobros,
        "obtener_pagos_por_concepto",
        lambda _cursor, _estudiante_id, hoy=None: ({}, {}, {}),
    )

    opciones = cobros.obtener_cuotas_vencidas_estudiante(CursorEspia(todas=[[]]), 7)

    assert [cuota["periodo"] for cuota in opciones[0]["cuotas"]] == [
        "2026-07-01",
        "2026-08-01",
        "2026-09-01",
    ]


def test_los_adelantos_maduros_se_cortan_en_el_mes_de_colombia(reloj):
    """Los adelantos aplicados cuentan como pagados hasta el mes en curso."""
    reloj(NOCHE_DEL_30)
    cursor = CursorEspia(una=[(1,)], todas=[[], [], []])

    cobros.obtener_pagos_por_concepto_estudiantes(cursor, (7,))

    _, params = cursor.ejecutadas[-1]
    assert params == ((7,), date(2026, 9, 1))


# ---------------------------------------------------------------------------
# Guardia: que no vuelva el reloj del servidor
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archivo", ["app/services/cobros.py", "app/services/cartera.py"])
def test_cobros_y_cartera_no_usan_el_reloj_del_servidor(archivo):
    fuente = (RAIZ / archivo).read_text(encoding="utf-8")

    assert "date.today()" not in fuente
    assert "datetime.now(" not in fuente
