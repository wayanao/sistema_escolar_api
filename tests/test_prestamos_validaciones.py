from datetime import date

from app.controllers import prestamo_controller
from app.routes import prestamos


def test_prestamos_route_filters_by_profesor(monkeypatch):
    calls = []

    def fake_obtener(profesor_id=None):
        calls.append(profesor_id)
        return []

    monkeypatch.setattr(prestamos, "obtener_prestamos", fake_obtener)

    response = prestamos.get_prestamos(profesor_id=12)

    assert response == []
    assert calls == [12]


def test_prestamos_route_rejects_negative_amount():
    prestamo = prestamos.PrestamoCreate(profesor_id=1, monto=-1)

    try:
        prestamos.add_prestamo(prestamo)
    except Exception as exc:
        assert exc.status_code == 400
        assert "mayor que 0" in exc.detail
    else:
        raise AssertionError("Expected negative loan amount to be rejected")


def test_prestamos_route_rejects_zero_amount():
    prestamo = prestamos.PrestamoCreate(profesor_id=1, monto=0)

    try:
        prestamos.add_prestamo(prestamo)
    except Exception as exc:
        assert exc.status_code == 400
        assert "mayor que 0" in exc.detail
    else:
        raise AssertionError("Expected zero loan amount to be rejected")


def test_prestamos_route_rejects_missing_profesor():
    prestamo = prestamos.PrestamoCreate(profesor_id=0, monto=1000)

    try:
        prestamos.add_prestamo(prestamo)
    except Exception as exc:
        assert exc.status_code == 400
        assert "profesor" in exc.detail
    else:
        raise AssertionError("Expected missing professor to be rejected")


def test_prestamos_route_rejects_non_pending_create_state():
    prestamo = prestamos.PrestamoCreate(profesor_id=1, monto=1000, estado="Pagado")

    try:
        prestamos.add_prestamo(prestamo)
    except Exception as exc:
        assert exc.status_code == 400
        assert "Pendiente" in exc.detail
    else:
        raise AssertionError("Expected paid initial state to be rejected")


def test_prestamo_normalization_defaults_date_and_trims_notes():
    prestamo = prestamos.PrestamoCreate(
        profesor_id=1,
        monto=1000,
        notas="  Descuento acordado  ",
    )

    normalizado = prestamo_controller._normalizar_prestamo(prestamo)

    assert normalizado == {
        "profesor_id": 1,
        "monto": 1000.0,
        "fecha": date.today(),
        "estado": "Pendiente",
        "notas": "Descuento acordado",
    }


class FakePrestamoCursor:
    def __init__(self, rowcount=1):
        self.rowcount = rowcount
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def close(self):
        pass


class FakePrestamoConnection:
    def __init__(self, rowcount=1):
        self.cursor_instance = FakePrestamoCursor(rowcount=rowcount)
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def close(self):
        pass


def test_actualizar_estado_only_allows_saldar(monkeypatch):
    conn = FakePrestamoConnection()
    monkeypatch.setattr(prestamo_controller, "get_connection", lambda: conn)

    response = prestamo_controller.actualizar_estado_prestamo(5, "Pagado")

    assert response == {"mensaje": "Estado actualizado a Pagado"}
    assert conn.committed is True
    assert conn.cursor_instance.executed[0][1] == ("Pagado", 5)


def test_actualizar_estado_rejects_other_states():
    try:
        prestamo_controller.actualizar_estado_prestamo(5, "Pendiente")
    except ValueError as exc:
        assert "saldar" in str(exc)
    else:
        raise AssertionError("Expected non-paid state to be rejected")


def test_prestamos_delete_is_blocked():
    try:
        prestamos.delete_prestamo(5)
    except Exception as exc:
        assert exc.status_code == 405
        assert "no se eliminan" in exc.detail
    else:
        raise AssertionError("Expected loan deletion to be blocked")
