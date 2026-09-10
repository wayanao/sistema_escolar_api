import datetime
from types import SimpleNamespace

from app.controllers import pagos_controller
from app.schemas.pago import PagoCreate
from app.services import cobros
from app.services.cartera import (
    calcular_cuotas_vencidas,
    calcular_deuda_concepto,
    listar_cuotas_vencidas,
)


class FakeCursor:
    def __init__(self, fetches=None):
        self.fetches = list(fetches or [])
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetches.pop(0)

    def fetchall(self):
        return self.fetches.pop(0)

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def _concepto_mensual():
    return {
        "id": 4,
        "nombre": "Pensión",
        "valor_unitario": 100.0,
        "valor_origen": "curso",
        "mes_inicial": 2,
        "frecuencia_meses": 1,
        "dia_limite_mes": 1,
        "dias_gracia": 0,
    }


def test_listar_cuotas_vencidas_devuelve_periodos_y_fechas_limite():
    cuotas = listar_cuotas_vencidas(
        hoy=datetime.date(2026, 4, 2),
        mes_inicial=2,
        frecuencia_meses=1,
        dia_limite_mes=5,
        dias_gracia=2,
        max_cuotas=12,
    )

    assert [cuota.periodo for cuota in cuotas] == [
        datetime.date(2026, 2, 1),
        datetime.date(2026, 3, 1),
    ]
    assert cuotas[0].fecha_vencimiento == datetime.date(2026, 2, 5)


def test_mensualidad_febrero_noviembre_no_genera_cuota_de_diciembre():
    cuotas = listar_cuotas_vencidas(
        hoy=datetime.date(2026, 12, 31),
        mes_inicial=2,
        mes_final=11,
        frecuencia_meses=1,
        dia_limite_mes=1,
        max_cuotas=12,
    )

    assert [cuota.periodo.month for cuota in cuotas] == list(range(2, 12))

    deuda = calcular_deuda_concepto(
        valor_unitario=100,
        tipo_cobro="mensual",
        pagado=0,
        hoy=datetime.date(2026, 12, 31),
        mes_inicial=2,
        mes_final=11,
        frecuencia_meses=1,
        dia_limite_mes=1,
        max_cuotas=12,
    )
    assert deuda["cuotas_vencidas"] == 10
    assert deuda["valor_total"] == 1000


def test_proxima_fecha_no_anuncia_diciembre_despues_del_ultimo_mes():
    resultado = calcular_cuotas_vencidas(
        hoy=datetime.date(2026, 11, 30),
        mes_inicial=2,
        mes_final=11,
        frecuencia_meses=1,
        dia_limite_mes=1,
        max_cuotas=12,
    )

    assert resultado.cuotas_vencidas == 10
    assert resultado.proxima_fecha is None
    assert resultado.proxima_cuota_pendiente is False


def test_opciones_vencidas_aplican_legacy_fifo_y_respetan_abono_explicito(monkeypatch):
    cursor = FakeCursor(fetches=[[
        (4, datetime.date(2026, 3, 1), 50),
    ]])
    monkeypatch.setattr(
        cobros,
        "obtener_conceptos_mensuales_estudiante",
        lambda _cursor, _estudiante_id: [_concepto_mensual()],
    )
    monkeypatch.setattr(
        cobros,
        "obtener_pagos_por_concepto",
        lambda _cursor, _estudiante_id, hoy=None: ({}, {"pensión": 100}, {}),
    )

    opciones = cobros.obtener_cuotas_vencidas_estudiante(
        cursor,
        7,
        hoy=datetime.date(2026, 4, 2),
    )

    assert opciones[0]["tipo_pago_id"] == 4
    assert opciones[0]["cuotas"] == [
        {
            "periodo": "2026-03-01",
            "fecha_vencimiento": "2026-03-01",
            "valor_cuota": 100.0,
            "saldo": 50.0,
            "estado": "parcial",
        },
        {
            "periodo": "2026-04-01",
            "fecha_vencimiento": "2026-04-01",
            "valor_cuota": 100.0,
            "saldo": 100.0,
            "estado": "vencido",
        },
    ]


def test_preparar_aplicaciones_valida_total_y_saldo_en_servidor(monkeypatch):
    cursor = FakeCursor(fetches=[(1,), (1,)])
    monkeypatch.setattr(
        pagos_controller,
        "obtener_cuotas_vencidas_estudiante",
        lambda _cursor, _estudiante_id, hoy=None: [{
            "tipo_pago_id": 4,
            "concepto": "Pensión",
            "cuotas": [{"periodo": "2026-03-01", "saldo": 100}],
        }],
    )
    pago = SimpleNamespace(
        estudiante_id=7,
        descripcion="Pensión",
        venta_id=None,
        monto=100,
        metodos=[SimpleNamespace(tipo="efectivo", monto=100, nota="")],
        aplicaciones=[SimpleNamespace(
            tipo_pago_id=4,
            periodo=datetime.date(2026, 3, 1),
            monto=100,
        )],
    )

    resultado = pagos_controller._preparar_aplicaciones_pago(
        cursor,
        pago,
        hoy=datetime.date(2026, 4, 2),
    )

    assert resultado["concepto"] == "Pensión"
    assert resultado["items"][0]["etiqueta"] == "Marzo 2026"
    assert any("pg_advisory_xact_lock" in query for query, _params in cursor.executed)


def test_distribuir_pago_mixto_conserva_pago_y_periodo():
    cursor = FakeCursor()
    pagos_controller._insertar_aplicaciones_distribuidas(
        cursor,
        [(81, 150), (82, 50)],
        [
            {
                "estudiante_id": 7,
                "tipo_pago_id": 4,
                "periodo": datetime.date(2026, 2, 1),
                "monto": 100,
            },
            {
                "estudiante_id": 7,
                "tipo_pago_id": 4,
                "periodo": datetime.date(2026, 3, 1),
                "monto": 100,
            },
        ],
    )

    inserts = [params for query, params in cursor.executed if "INSERT INTO pagos_aplicaciones" in query]
    assert inserts == [
        (81, 7, 4, datetime.date(2026, 2, 1), 100.0),
        (81, 7, 4, datetime.date(2026, 3, 1), 50.0),
        (82, 7, 4, datetime.date(2026, 3, 1), 50.0),
    ]


def test_pago_create_sigue_admitiendo_flujo_anterior_sin_aplicaciones():
    pago = PagoCreate(
        estudiante_id=7,
        descripcion="Matrícula",
        monto=100,
        metodos=[{"tipo": "efectivo", "monto": 100}],
    )

    assert pago.aplicaciones is None
