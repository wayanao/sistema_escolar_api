import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.controllers import pagos_controller, reportes_controller
from app.schemas.pago import PagoAdelantadoCreate
from app.services.cobros import _calcular_deudas


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
        "valor_unitario": 300000.0,
        "valor_origen": "curso",
        "mes_inicial": 2,
        "frecuencia_meses": 1,
    }


def test_schema_adelanto_exige_metodos_positivos():
    with pytest.raises(ValidationError):
        PagoAdelantadoCreate(
            estudiante_id=1,
            tipo_pago_id=4,
            cantidad_meses=2,
            metodos=[{"tipo": "efectivo", "monto": 0}],
        )


def test_periodos_programados_solo_incluye_meses_futuros_del_anio():
    periodos = pagos_controller._periodos_programados(
        _concepto_mensual(),
        datetime.date(2026, 7, 16),
    )

    assert periodos == [
        datetime.date(2026, mes, 1)
        for mes in range(8, 13)
    ]


def test_registrar_adelanto_crea_un_pago_y_una_aplicacion_por_mes(monkeypatch):
    cursor = FakeCursor(fetches=[(81,)])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(pagos_controller, "_exigir_tabla_pagos_aplicaciones", lambda _cursor: None)
    monkeypatch.setattr(
        pagos_controller,
        "obtener_conceptos_mensuales_estudiante",
        lambda _cursor, _estudiante_id: [_concepto_mensual()],
    )
    monkeypatch.setattr(
        pagos_controller,
        "_periodos_disponibles",
        lambda _cursor, _estudiante_id, _concepto, _hoy: [
            datetime.date(2026, 8, 1),
            datetime.date(2026, 9, 1),
            datetime.date(2026, 10, 1),
        ],
    )
    pago = SimpleNamespace(
        estudiante_id=7,
        tipo_pago_id=4,
        cantidad_meses=2,
        fecha=datetime.date(2026, 7, 16),
        metodos=[SimpleNamespace(tipo="transferencia", monto=600000, nota="Banco")],
    )

    resultado = pagos_controller.registrar_pago_adelantado_controller(
        pago,
        hoy=datetime.date(2026, 7, 16),
    )

    inserts_pago = [item for item in cursor.executed if "INSERT INTO pagos (" in item[0]]
    inserts_aplicacion = [item for item in cursor.executed if "INSERT INTO pagos_aplicaciones" in item[0]]
    assert len(inserts_pago) == 1
    assert inserts_pago[0][1][1] == 600000.0
    assert len(inserts_aplicacion) == 2
    assert [item[1][3] for item in inserts_aplicacion] == [
        datetime.date(2026, 8, 1),
        datetime.date(2026, 9, 1),
    ]
    assert resultado["pago_id"] == 81
    assert resultado["monto"] == 600000.0
    assert conn.committed is True
    assert conn.rolled_back is False
    assert cursor.closed is True
    assert conn.closed is True


def test_registrar_adelanto_rechaza_metodos_que_no_suman_total(monkeypatch):
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(pagos_controller, "_exigir_tabla_pagos_aplicaciones", lambda _cursor: None)
    monkeypatch.setattr(
        pagos_controller,
        "obtener_conceptos_mensuales_estudiante",
        lambda _cursor, _estudiante_id: [_concepto_mensual()],
    )
    monkeypatch.setattr(
        pagos_controller,
        "_periodos_disponibles",
        lambda *_args: [datetime.date(2026, 8, 1), datetime.date(2026, 9, 1)],
    )
    pago = SimpleNamespace(
        estudiante_id=7,
        tipo_pago_id=4,
        cantidad_meses=2,
        fecha=None,
        metodos=[SimpleNamespace(tipo="efectivo", monto=300000, nota="")],
    )

    with pytest.raises(ValueError, match="suma de los métodos"):
        pagos_controller.registrar_pago_adelantado_controller(
            pago,
            hoy=datetime.date(2026, 7, 16),
        )

    assert not any("INSERT INTO pagos (" in query for query, _params in cursor.executed)
    assert conn.rolled_back is True
    assert conn.committed is False


def test_aplicacion_vencida_se_suma_sin_reemplazar_pago_normal():
    resultado = _calcular_deudas(
        tipos_pago=[{
            "id": 4,
            "nombre": "Pensión",
            "valor": 100,
            "tipo_cobro": "mensual",
            "activo": True,
            "mes_inicial": 2,
            "frecuencia_meses": 1,
            "dia_limite_mes": 1,
            "dias_gracia": 0,
            "mora_tipo": None,
            "mora_valor": 0,
        }],
        asignaciones_curso={4: 100},
        pagos_nombre={},
        pagos_descripcion={"pensión": 100},
        pagos_aplicados={"pensión": 100},
        hoy=datetime.date(2026, 3, 2),
    )

    assert resultado["deudas"][0]["pagado"] == 200
    assert resultado["deudas"][0]["deuda"] == 0


def test_anular_adelanto_libera_sus_periodos(monkeypatch):
    cursor = FakeCursor(fetches=[
        (81, "Pagado", 600000, None, "Pensión · Pago adelantado"),
        (1,),
    ])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conn)

    resultado = pagos_controller.anular_pago_controller(81, "Acuerdo cancelado", 9)

    updates_aplicaciones = [
        params
        for query, params in cursor.executed
        if "UPDATE pagos_aplicaciones" in query
    ]
    assert updates_aplicaciones == [(81,)]
    assert resultado == {"mensaje": "Pago anulado correctamente", "pago_id": 81}
    assert conn.committed is True


def test_reporte_curso_aplica_solo_adelantos_maduros_y_no_los_duplica(monkeypatch):
    cursor = FakeCursor(fetches=[
        [(7, "Ana", "Díaz")],
        [],
        [],
        (0,),
    ])
    conn = FakeConnection(cursor)
    tipo_pago = {
        "id": 4,
        "nombre": "Pensión",
        "valor": 100,
        "tipo_cobro": "mensual",
        "activo": True,
    }
    monkeypatch.setattr(reportes_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(reportes_controller, "obtener_tipos_pago", lambda _cursor: [tipo_pago])
    monkeypatch.setattr(
        reportes_controller,
        "obtener_asignaciones_cobro_por_curso",
        lambda _cursor, _curso_id: {4: 100},
    )
    monkeypatch.setattr(
        reportes_controller,
        "obtener_pagos_por_concepto_estudiantes",
        lambda _cursor, _ids: ({}, {}, {7: {"pensión": 100}}),
    )
    monkeypatch.setattr(
        reportes_controller,
        "tabla_pagos_aplicaciones_existe",
        lambda _cursor: True,
    )
    monkeypatch.setattr(
        reportes_controller,
        "obtener_valores_personalizados_estudiante",
        lambda _cursor, _estudiante_id: {},
    )

    def calcular_resumen(**contexto):
        assert contexto["pagos_aplicados"] == {"pensión": 100}
        return {
            "deudas": [{
                "concepto_id": 4,
                "concepto": "Pensión",
                "valor_total": 200,
                "pagado": 100,
                "deuda": 100,
                "mora": 0,
                "cuotas_vencidas": 2,
            }]
        }

    monkeypatch.setattr(
        reportes_controller,
        "calcular_deudas_desde_contexto",
        calcular_resumen,
    )

    resultado = reportes_controller.reporte_estado_cuenta_curso_controller(3)

    consulta_otros = next(
        query for query, _params in cursor.executed if "concepto_id IS NULL" in query
    )
    assert "NOT EXISTS" in consulta_otros
    assert resultado[0]["pagado"] == 100
    assert resultado[0]["deudas_detalle"] == [{
        "concepto": "Pensión",
        "valor_total": 200,
        "pagado": 100,
        "deuda": 100,
        "mora": 0,
        "cuotas_vencidas": 2,
    }]
