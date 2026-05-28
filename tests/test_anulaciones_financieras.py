import datetime

from app.controllers import pagos_controller, reportes_controller, venta_controller


class FakeCursor:
    def __init__(self, fetches):
        self.fetches = list(fetches)
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


def _sql(cursor):
    return "\n".join(query for query, _params in cursor.executed)


def test_anular_pago_academico_no_toca_ventas(monkeypatch):
    cursor = FakeCursor([
        (10, "Pagado", 50000, None, "Mensualidad mayo"),
    ])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conn)

    response = pagos_controller.anular_pago_controller(10, "Error de caja", 7)

    assert response == {"mensaje": "Pago anulado correctamente", "pago_id": 10}
    assert conn.committed is True
    assert conn.rolled_back is False
    assert "UPDATE pagos" in _sql(cursor)
    assert "UPDATE ventas" not in _sql(cursor)
    update_pago = cursor.executed[-1]
    assert update_pago[1][0] == "Error de caja"
    assert update_pago[1][2] == 7
    assert update_pago[1][3] == 10


def test_anular_pago_inventario_descuenta_abono_de_venta(monkeypatch):
    cursor = FakeCursor([
        (11, "Pagado", 40000, 5, "Cargo de Inventario #5"),
        (5, 100000, 40000),
    ])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conn)

    response = pagos_controller.anular_pago_controller(11, "Pago equivocado", 7)

    assert response == {"mensaje": "Pago anulado correctamente", "pago_id": 11}
    assert conn.committed is True
    ventas_updates = [params for query, params in cursor.executed if "UPDATE ventas" in query]
    assert ventas_updates == [(0.0, "Pendiente", 5)]


def test_anular_venta_anula_pagos_y_regresa_stock(monkeypatch):
    cursor = FakeCursor([
        (5, "Pendiente"),
        [(2, 3), (9, 1)],
    ])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(venta_controller, "get_connection", lambda: conn)

    response = venta_controller.anular_venta(5, "Cliente devolvio compra", 7)

    assert response == {"mensaje": "Venta anulada correctamente", "venta_id": 5}
    assert conn.committed is True
    stock_updates = [params for query, params in cursor.executed if "UPDATE inventario" in query]
    assert stock_updates == [(3, 2), (1, 9)]
    sql = _sql(cursor)
    assert "UPDATE pagos" in sql
    assert "estado = 'Anulado'" in sql
    venta_updates = [params for query, params in cursor.executed if "UPDATE ventas" in query]
    assert venta_updates[0][0] == "Cliente devolvio compra"
    assert venta_updates[0][2] == 7
    assert venta_updates[0][3] == 5


def test_formatear_ingreso_anulado_no_suma_como_monto_valido():
    fecha = datetime.datetime(2026, 5, 27, 10, 30)
    row = (
        20,
        "Ana",
        "Perez",
        60000,
        fecha,
        "Mensualidad",
        "Mensualidad",
        "Anulado",
        "Error de caja",
        fecha,
    )

    ingreso = reportes_controller._formatear_ingreso(row)

    assert ingreso["anulado"] is True
    assert ingreso["monto"] == 60000.0
    assert ingreso["monto_valido"] == 0
    assert ingreso["motivo_anulacion"] == "Error de caja"


def test_reporte_general_excluye_pagos_anulados_de_totales(monkeypatch):
    cursor = FakeCursor([
        (3, 2, 1, 4, 120000, 50000),
        [],
        [],
    ])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(reportes_controller, "get_connection", lambda: conn)

    response = reportes_controller.reporte_general_controller()

    assert response["estadisticas_generales"]["total_ingresos"] == 120000.0
    assert response["estadisticas_generales"]["ingresos_hoy"] == 50000.0
    sql = _sql(cursor)
    assert "COALESCE(estado, 'Pagado') <> 'Anulado'" in sql
    assert "America/Bogota" in sql
    assert "CASE WHEN COALESCE(estado, 'Pagado') = 'Anulado' THEN 0 ELSE monto END" in sql
