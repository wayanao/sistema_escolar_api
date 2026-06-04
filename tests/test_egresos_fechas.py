from datetime import date

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
