from datetime import date

from app.controllers import egreso_controller
from app.routes import egresos


def test_egresos_route_defaults_to_today(monkeypatch):
    calls = []

    def fake_obtener(fecha_desde=None, fecha_hasta=None):
        calls.append((fecha_desde, fecha_hasta))
        return []

    monkeypatch.setattr(egresos, "obtener_egresos", fake_obtener)

    response = egresos.get_egresos()

    assert response == []
    assert calls == [(date.today(), date.today())]


def test_egresos_route_uses_date_range(monkeypatch):
    calls = []

    def fake_obtener(fecha_desde=None, fecha_hasta=None):
        calls.append((fecha_desde, fecha_hasta))
        return [{"id": 1}]

    monkeypatch.setattr(egresos, "obtener_egresos", fake_obtener)

    response = egresos.get_egresos(
        fecha_desde=date(2026, 6, 1),
        fecha_hasta=date(2026, 6, 3),
    )

    assert response == [{"id": 1}]
    assert calls == [(date(2026, 6, 1), date(2026, 6, 3))]


def test_egresos_route_rejects_invalid_date_range():
    try:
        egresos.get_egresos(
            fecha_desde=date(2026, 6, 3),
            fecha_hasta=date(2026, 6, 1),
        )
    except Exception as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("Expected invalid date range to be rejected")


def test_egresos_delete_is_blocked():
    try:
        egresos.delete_egreso(9)
    except Exception as exc:
        assert exc.status_code == 405
        assert "no se eliminan" in exc.detail
    else:
        raise AssertionError("Expected egreso deletion to be blocked")


def test_egresos_route_rejects_negative_amount():
    egreso = egresos.EgresoCreate(concepto="Compra de papeleria", monto=-1)

    try:
        egresos.add_egreso(egreso)
    except Exception as exc:
        assert exc.status_code == 400
        assert "mayor que 0" in exc.detail
    else:
        raise AssertionError("Expected negative egreso amount to be rejected")


def test_egresos_route_rejects_zero_amount():
    egreso = egresos.EgresoCreate(concepto="Compra de papeleria", monto=0)

    try:
        egresos.add_egreso(egreso)
    except Exception as exc:
        assert exc.status_code == 400
        assert "mayor que 0" in exc.detail
    else:
        raise AssertionError("Expected zero egreso amount to be rejected")


def test_egresos_route_rejects_empty_concept():
    egreso = egresos.EgresoCreate(concepto="   ", monto=1500)

    try:
        egresos.add_egreso(egreso)
    except Exception as exc:
        assert exc.status_code == 400
        assert "concepto" in exc.detail
    else:
        raise AssertionError("Expected empty egreso concept to be rejected")


def test_egreso_normalization_defaults_date_and_trims_text():
    egreso = egresos.EgresoCreate(
        concepto="  Compra de papeleria  ",
        monto=1500,
        categoria="  Otros  ",
        notas="  Factura 123  ",
    )

    normalizado = egreso_controller._normalizar_egreso(egreso)

    assert normalizado == {
        "concepto": "Compra de papeleria",
        "monto": 1500.0,
        "fecha": date.today(),
        "categoria": "Otros",
        "notas": "Factura 123",
    }


class FakeEgresoCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.rows.pop(0)

    def close(self):
        pass


class FakeEgresoConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeEgresoCursor(rows)
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def close(self):
        pass


def test_actualizar_egreso_allows_manual_origin(monkeypatch):
    conn = FakeEgresoConnection(rows=[("manual",), (7,)])
    monkeypatch.setattr(egreso_controller, "get_connection", lambda: conn)
    egreso = egresos.EgresoCreate(
        concepto="  Compra editada  ",
        monto=2200,
        fecha=date(2026, 6, 4),
        categoria="  Otros  ",
        notas="  Ajuste factura  ",
    )

    response = egreso_controller.actualizar_egreso(7, egreso)

    assert response == {"id": 7, "mensaje": "Egreso actualizado exitosamente"}
    assert conn.committed is True
    assert conn.cursor_instance.executed[1][1] == (
        "Compra editada",
        2200.0,
        date(2026, 6, 4),
        "Otros",
        "Ajuste factura",
        7,
    )


def test_actualizar_egreso_rejects_non_manual_origin(monkeypatch):
    conn = FakeEgresoConnection(rows=[("nomina",)])
    monkeypatch.setattr(egreso_controller, "get_connection", lambda: conn)
    egreso = egresos.EgresoCreate(concepto="Pago nomina editado", monto=2200)

    try:
        egreso_controller.actualizar_egreso(7, egreso)
    except PermissionError as exc:
        assert "manualmente" in str(exc)
        assert conn.committed is False
    else:
        raise AssertionError("Expected non-manual egreso to be rejected")


def test_update_egreso_route_maps_non_manual_to_403(monkeypatch):
    def fake_actualizar(egreso_id, datos):
        raise PermissionError("Solo se pueden editar egresos creados manualmente en esta pantalla.")

    monkeypatch.setattr(egresos, "actualizar_egreso", fake_actualizar)
    egreso = egresos.EgresoCreate(concepto="Pago nomina editado", monto=2200)

    try:
        egresos.update_egreso(7, egreso)
    except Exception as exc:
        assert exc.status_code == 403
        assert "manualmente" in exc.detail
    else:
        raise AssertionError("Expected update route to reject non-manual egreso")
