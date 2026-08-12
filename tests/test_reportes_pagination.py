import inspect

import pytest
from fastapi import HTTPException

from app.routes import reportes


def test_reporte_general_keeps_controller_response(monkeypatch):
    expected = {"ingresos": 1200, "egresos": 300}
    calls = []

    def fake_reporte_general_controller():
        calls.append(())
        return expected

    monkeypatch.setattr(
        reportes,
        "reporte_general_controller",
        fake_reporte_general_controller,
    )

    response = reportes.reporte_general()

    assert response == expected
    assert calls == [()]


def test_reporte_estado_cuenta_curso_delegates_course_id(monkeypatch):
    expected = [{"estudiante_id": 9, "saldo": 500}]
    calls = []

    def fake_reporte_estado_cuenta_curso_controller(curso_id):
        calls.append(curso_id)
        return expected

    monkeypatch.setattr(
        reportes,
        "reporte_estado_cuenta_curso_controller",
        fake_reporte_estado_cuenta_curso_controller,
    )

    response = reportes.reporte_estado_cuenta_curso(17)

    assert response == expected
    assert calls == [17]


@pytest.mark.parametrize(
    ("route_name", "controller_name", "args"),
    [
        ("reporte_general", "reporte_general_controller", ()),
        (
            "reporte_estado_cuenta_curso",
            "reporte_estado_cuenta_curso_controller",
            (17,),
        ),
        ("reporte_ingresos_mes", "reporte_ingresos_mes_controller", ("2026-05",)),
        (
            "reporte_ingresos_rango",
            "reporte_ingresos_rango_controller",
            ("2026-05-01", "2026-05-31"),
        ),
        (
            "reporte_egresos_rango",
            "reporte_egresos_rango_controller",
            ("2026-05-01", "2026-05-31"),
        ),
    ],
)
def test_report_routes_translate_controller_errors(
    monkeypatch,
    route_name,
    controller_name,
    args,
):
    def fail_controller(*_args, **_kwargs):
        raise ValueError("fallo-controlado")

    monkeypatch.setattr(reportes, controller_name, fail_controller)

    with pytest.raises(HTTPException) as exc:
        getattr(reportes, route_name)(*args)

    assert exc.value.status_code == 400
    assert exc.value.detail == "fallo-controlado"


def test_reporte_ingresos_mes_keeps_legacy_list_response(monkeypatch):
    def fake_reporte_ingresos_mes_controller(mes, limit=None, offset=0):
        return [{"id": 1, "mes": mes, "limit": limit, "offset": offset}]

    monkeypatch.setattr(
        reportes,
        "reporte_ingresos_mes_controller",
        fake_reporte_ingresos_mes_controller,
    )

    response = reportes.reporte_ingresos_mes("2026-05")

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

    response = reportes.reporte_ingresos_mes("2026-05", limit=25, offset=50)

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

    response = reportes.reporte_ingresos_rango("2026-05-01", "2026-05-31")

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

    response = reportes.reporte_ingresos_rango(
        "2026-05-01",
        "2026-05-31",
        limit=25,
        offset=50,
    )

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{
        "inicio": "2026-05-01",
        "fin": "2026-05-31",
        "limit": 25,
        "offset": 50,
    }]


def test_reporte_egresos_rango_keeps_legacy_list_response(monkeypatch):
    def fake_reporte_egresos_rango_controller(inicio, fin, limit=None, offset=0):
        return [{"id": 1, "inicio": inicio, "fin": fin, "limit": limit, "offset": offset}]

    monkeypatch.setattr(
        reportes,
        "reporte_egresos_rango_controller",
        fake_reporte_egresos_rango_controller,
    )

    response = reportes.reporte_egresos_rango("2026-05-01", "2026-05-31")

    assert response == [{
        "id": 1,
        "inicio": "2026-05-01",
        "fin": "2026-05-31",
        "limit": None,
        "offset": 0,
    }]


def test_reporte_egresos_rango_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_reporte_egresos_rango_controller(inicio, fin, limit=None, offset=0):
        calls.append({"inicio": inicio, "fin": fin, "limit": limit, "offset": offset})
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(
        reportes,
        "reporte_egresos_rango_controller",
        fake_reporte_egresos_rango_controller,
    )

    response = reportes.reporte_egresos_rango(
        "2026-05-01",
        "2026-05-31",
        limit=25,
        offset=50,
    )

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{
        "inicio": "2026-05-01",
        "fin": "2026-05-31",
        "limit": 25,
        "offset": 50,
    }]


@pytest.mark.parametrize(
    "route",
    [
        reportes.reporte_general,
        reportes.reporte_estado_cuenta_curso,
        reportes.reporte_ingresos_mes,
        reportes.reporte_ingresos_rango,
        reportes.reporte_egresos_rango,
    ],
)
def test_report_routes_are_sync_for_fastapi_threadpool(route):
    assert not inspect.iscoroutinefunction(route)
