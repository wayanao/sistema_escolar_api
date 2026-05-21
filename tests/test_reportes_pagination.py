import asyncio

from app.routes import reportes


def test_reporte_ingresos_mes_keeps_legacy_list_response(monkeypatch):
    def fake_reporte_ingresos_mes_controller(mes, limit=None, offset=0):
        return [{"id": 1, "mes": mes, "limit": limit, "offset": offset}]

    monkeypatch.setattr(
        reportes,
        "reporte_ingresos_mes_controller",
        fake_reporte_ingresos_mes_controller,
    )

    response = asyncio.run(reportes.reporte_ingresos_mes("2026-05"))

    assert response == [{"id": 1, "mes": "2026-05", "limit": None, "offset": 0}]


def test_reporte_ingresos_mes_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_reporte_ingresos_mes_controller(mes, limit=None, offset=0):
        calls.append({"mes": mes, "limit": limit, "offset": offset})
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(
        reportes,
        "reporte_ingresos_mes_controller",
        fake_reporte_ingresos_mes_controller,
    )

    response = asyncio.run(reportes.reporte_ingresos_mes("2026-05", limit=25, offset=50))

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{"mes": "2026-05", "limit": 25, "offset": 50}]


def test_reporte_ingresos_rango_keeps_legacy_list_response(monkeypatch):
    def fake_reporte_ingresos_rango_controller(inicio, fin, limit=None, offset=0):
        return [{"id": 1, "inicio": inicio, "fin": fin, "limit": limit, "offset": offset}]

    monkeypatch.setattr(
        reportes,
        "reporte_ingresos_rango_controller",
        fake_reporte_ingresos_rango_controller,
    )

    response = asyncio.run(reportes.reporte_ingresos_rango("2026-05-01", "2026-05-31"))

    assert response == [{
        "id": 1,
        "inicio": "2026-05-01",
        "fin": "2026-05-31",
        "limit": None,
        "offset": 0,
    }]


def test_reporte_ingresos_rango_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_reporte_ingresos_rango_controller(inicio, fin, limit=None, offset=0):
        calls.append({"inicio": inicio, "fin": fin, "limit": limit, "offset": offset})
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(
        reportes,
        "reporte_ingresos_rango_controller",
        fake_reporte_ingresos_rango_controller,
    )

    response = asyncio.run(
        reportes.reporte_ingresos_rango(
            "2026-05-01",
            "2026-05-31",
            limit=25,
            offset=50,
        )
    )

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{
        "inicio": "2026-05-01",
        "fin": "2026-05-31",
        "limit": 25,
        "offset": 50,
    }]
