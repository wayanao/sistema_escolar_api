"""Caracterizacion de los cinco GET de plan de clases migrados en 2.3a."""

from collections import Counter
from datetime import date
import inspect

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute

from app.dependencies import get_current_active_admin, get_current_user
from app.routes import plan_de_clases


TARGET_ROUTES = {
    "/notificaciones/planeadores": (
        plan_de_clases.obtener_notificaciones_planeadores,
        get_current_user,
    ),
    "/plan-de-clases/{asignacion_id}": (
        plan_de_clases.obtener_planes_por_asignacion,
        get_current_user,
    ),
    "/admin/plan-de-clases": (
        plan_de_clases.listar_planes_admin,
        get_current_active_admin,
    ),
    "/admin/plan-de-clases/{plan_id}": (
        plan_de_clases.obtener_plan_admin,
        get_current_active_admin,
    ),
    "/plan-de-clases/{plan_id}/observaciones": (
        plan_de_clases.listar_observaciones_plan,
        get_current_user,
    ),
}


def _invoke(handler, *args, **kwargs):
    return handler(*args, **kwargs)


def _target_api_routes():
    endpoints = {endpoint for endpoint, _dependency in TARGET_ROUTES.values()}
    return [
        route
        for route in plan_de_clases.router.routes
        if isinstance(route, APIRoute) and route.endpoint in endpoints
    ]


def _openapi_parameter(operation, name, location):
    return next(
        parameter
        for parameter in operation["parameters"]
        if parameter["name"] == name and parameter["in"] == location
    )


def _nullable_non_null_schema(parameter):
    assert parameter["required"] is False
    schema = parameter["schema"]
    assert schema.get("default") is None
    options = schema.get("anyOf") or schema.get("oneOf")
    assert options is not None
    assert any(option.get("type") == "null" for option in options)
    non_null = [option for option in options if option.get("type") != "null"]
    assert len(non_null) == 1
    return non_null[0]


def test_target_routes_preserve_paths_methods_and_dependencies():
    routes = _target_api_routes()

    assert len(routes) == len(TARGET_ROUTES) == 5
    assert {route.path for route in routes} == set(TARGET_ROUTES)
    for route in routes:
        endpoint, dependency = TARGET_ROUTES[route.path]
        assert route.endpoint is endpoint
        assert route.methods == {"GET"}
        assert Counter(item.call for item in route.dependant.dependencies) == Counter(
            {dependency: 1}
        )


def test_target_registered_endpoints_are_sync():
    routes = _target_api_routes()

    assert len(routes) == len(TARGET_ROUTES) == 5
    assert all(not inspect.iscoroutinefunction(route.endpoint) for route in routes)


def test_target_routes_preserve_openapi_parameters():
    app = FastAPI()
    app.include_router(plan_de_clases.router)
    paths = app.openapi()["paths"]

    notifications_limit = _openapi_parameter(
        paths["/notificaciones/planeadores"]["get"], "limit", "query"
    )
    assert notifications_limit["required"] is False
    assert notifications_limit["schema"]["type"] == "integer"
    assert notifications_limit["schema"]["minimum"] == 1
    assert notifications_limit["schema"]["maximum"] == 20
    assert notifications_limit["schema"]["default"] == 8

    assignment = paths["/plan-de-clases/{asignacion_id}"]["get"]
    assignment_id = _openapi_parameter(assignment, "asignacion_id", "path")
    assert assignment_id["required"] is True
    assert assignment_id["schema"]["type"] == "integer"
    fecha = _nullable_non_null_schema(
        _openapi_parameter(assignment, "fecha", "query")
    )
    assert fecha["type"] == "string"
    assert fecha["format"] == "date"
    history_limit = _nullable_non_null_schema(
        _openapi_parameter(assignment, "limit", "query")
    )
    assert history_limit["type"] == "integer"
    assert history_limit["minimum"] == 1
    assert history_limit["maximum"] == 50
    history_offset = _openapi_parameter(assignment, "offset", "query")["schema"]
    assert _openapi_parameter(assignment, "offset", "query")["required"] is False
    assert history_offset["type"] == "integer"
    assert history_offset["minimum"] == 0
    assert history_offset["default"] == 0

    admin_list = paths["/admin/plan-de-clases"]["get"]
    profesor_id = _nullable_non_null_schema(
        _openapi_parameter(admin_list, "profesor_id", "query")
    )
    assert profesor_id["type"] == "integer"
    for name in ("fecha_desde", "fecha_hasta"):
        fecha_admin = _nullable_non_null_schema(
            _openapi_parameter(admin_list, name, "query")
        )
        assert fecha_admin["type"] == "string"
        assert fecha_admin["format"] == "date"
    busqueda = _nullable_non_null_schema(
        _openapi_parameter(admin_list, "busqueda", "query")
    )
    assert busqueda["type"] == "string"
    estados = _nullable_non_null_schema(
        _openapi_parameter(admin_list, "estado_revision", "query")
    )
    assert set(estados["enum"]) == {
        "pendiente",
        "visto",
        "con_observaciones",
        "revisado",
    }
    admin_limit_parameter = _openapi_parameter(admin_list, "limit", "query")
    assert admin_limit_parameter["required"] is False
    admin_limit = admin_limit_parameter["schema"]
    assert admin_limit["minimum"] == 1
    assert admin_limit["maximum"] == 100
    assert admin_limit["default"] == 50
    admin_offset_parameter = _openapi_parameter(admin_list, "offset", "query")
    assert admin_offset_parameter["required"] is False
    admin_offset = admin_offset_parameter["schema"]
    assert admin_offset["minimum"] == 0
    assert admin_offset["default"] == 0

    for path in (
        "/admin/plan-de-clases/{plan_id}",
        "/plan-de-clases/{plan_id}/observaciones",
    ):
        plan_id = _openapi_parameter(paths[path]["get"], "plan_id", "path")
        assert plan_id["required"] is True
        assert plan_id["schema"]["type"] == "integer"


@pytest.mark.parametrize("role", ["admin", "profesor"])
def test_notifications_delegate_allowed_roles_without_transforming_payload(
    monkeypatch, role
):
    current_user = {"id": 17, "rol": role, "tenant": "tenant_demo"}
    expected = {"total_no_leidas": 2, "items": [{"imagen1": "db/key.jpg"}]}
    observed = {}

    def fake_controller(*args, **kwargs):
        observed["args"] = args
        observed["kwargs"] = kwargs
        return expected

    monkeypatch.setattr(
        plan_de_clases,
        "obtener_notificaciones_planeadores_controller",
        fake_controller,
    )

    response = _invoke(
        plan_de_clases.obtener_notificaciones_planeadores,
        limit=6,
        current_user=current_user,
    )

    assert response is expected
    assert observed == {
        "args": (current_user,),
        "kwargs": {"limit": 6},
    }


def test_notifications_reject_unauthorized_role_before_controller(monkeypatch):
    monkeypatch.setattr(
        plan_de_clases,
        "obtener_notificaciones_planeadores_controller",
        lambda *_args, **_kwargs: pytest.fail("No debe consultar notificaciones"),
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.obtener_notificaciones_planeadores,
            limit=8,
            current_user={"id": 4, "rol": "estudiante"},
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "No autorizado"


def test_assignment_by_date_checks_access_and_delegates_only_day_branch(monkeypatch):
    current_user = {"id": 9, "rol": "profesor"}
    requested_date = date(2026, 8, 12)
    expected = {"id": 31, "imagen1": "tenant/plan.jpg", "imagen2": None}
    observed = []

    def fake_guard(asignacion_id, user, detail):
        observed.append(("guard", asignacion_id, user, detail))

    def fake_day(asignacion_id, fecha):
        observed.append(("day", asignacion_id, fecha))
        return expected

    monkeypatch.setattr(plan_de_clases, "require_asignacion_access", fake_guard)
    monkeypatch.setattr(plan_de_clases, "obtener_plan_del_dia_controller", fake_day)
    monkeypatch.setattr(
        plan_de_clases,
        "obtener_planes_por_asignacion_controller",
        lambda *_args, **_kwargs: pytest.fail("No debe consultar el historial"),
    )

    response = _invoke(
        plan_de_clases.obtener_planes_por_asignacion,
        asignacion_id=23,
        fecha=requested_date,
        limit=4,
        offset=7,
        current_user=current_user,
    )

    assert response is expected
    assert observed == [
        (
            "guard",
            23,
            current_user,
            "No tienes permisos para esta asignación",
        ),
        ("day", 23, requested_date),
    ]


def test_assignment_history_checks_access_and_preserves_pagination(monkeypatch):
    current_user = {"id": 9, "rol": "profesor"}
    expected = [{"id": 31, "imagen1": None, "imagen2": "tenant/plan.jpg"}]
    observed = []

    def fake_guard(asignacion_id, user, detail):
        observed.append(("guard", asignacion_id, user, detail))

    def fake_history(asignacion_id, *, limit, offset):
        observed.append(("history", asignacion_id, limit, offset))
        return expected

    monkeypatch.setattr(plan_de_clases, "require_asignacion_access", fake_guard)
    monkeypatch.setattr(
        plan_de_clases,
        "obtener_plan_del_dia_controller",
        lambda *_args, **_kwargs: pytest.fail("No debe consultar el día"),
    )
    monkeypatch.setattr(
        plan_de_clases,
        "obtener_planes_por_asignacion_controller",
        fake_history,
    )

    response = _invoke(
        plan_de_clases.obtener_planes_por_asignacion,
        asignacion_id=23,
        fecha=None,
        limit=4,
        offset=7,
        current_user=current_user,
    )

    assert response is expected
    assert observed == [
        (
            "guard",
            23,
            current_user,
            "No tienes permisos para esta asignación",
        ),
        ("history", 23, 4, 7),
    ]


def test_assignment_denial_stops_before_read_controllers(monkeypatch):
    current_user = {"id": 9, "rol": "profesor"}

    def deny(asignacion_id, user, detail):
        assert (asignacion_id, user, detail) == (
            23,
            current_user,
            "No tienes permisos para esta asignación",
        )
        raise HTTPException(status_code=403, detail=detail)

    monkeypatch.setattr(plan_de_clases, "require_asignacion_access", deny)
    monkeypatch.setattr(
        plan_de_clases,
        "obtener_plan_del_dia_controller",
        lambda *_args, **_kwargs: pytest.fail("No debe consultar el día"),
    )
    monkeypatch.setattr(
        plan_de_clases,
        "obtener_planes_por_asignacion_controller",
        lambda *_args, **_kwargs: pytest.fail("No debe consultar el historial"),
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.obtener_planes_por_asignacion,
            asignacion_id=23,
            fecha=None,
            limit=None,
            offset=0,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "No tienes permisos para esta asignación"


@pytest.mark.parametrize("use_date", [False, True])
def test_assignment_read_errors_keep_400_and_detail(monkeypatch, use_date):
    monkeypatch.setattr(
        plan_de_clases,
        "require_asignacion_access",
        lambda *_args, **_kwargs: None,
    )

    def fail(*_args, **_kwargs):
        raise ValueError("consulta fallida")

    monkeypatch.setattr(
        plan_de_clases,
        "obtener_plan_del_dia_controller",
        fail if use_date else lambda *_args: pytest.fail("Rama incorrecta"),
    )
    monkeypatch.setattr(
        plan_de_clases,
        "obtener_planes_por_asignacion_controller",
        (lambda *_args, **_kwargs: pytest.fail("Rama incorrecta")) if use_date else fail,
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.obtener_planes_por_asignacion,
            asignacion_id=23,
            fecha=date(2026, 8, 12) if use_date else None,
            limit=5,
            offset=0,
            current_user={"id": 9, "rol": "profesor"},
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "consulta fallida"


def test_admin_list_delegates_all_filters_without_transforming_payload(monkeypatch):
    expected = {"total": 1, "items": [{"id": 31, "imagen1": "db/key.jpg"}]}
    observed = {}

    def fake_controller(**filters):
        observed.update(filters)
        return expected

    monkeypatch.setattr(
        plan_de_clases,
        "listar_planes_admin_controller",
        fake_controller,
    )

    response = _invoke(
        plan_de_clases.listar_planes_admin,
        profesor_id=7,
        fecha_desde=date(2026, 8, 1),
        fecha_hasta=date(2026, 8, 12),
        busqueda="fracciones",
        estado_revision="con_observaciones",
        limit=25,
        offset=50,
    )

    assert response is expected
    assert observed == {
        "profesor_id": 7,
        "fecha_desde": date(2026, 8, 1),
        "fecha_hasta": date(2026, 8, 12),
        "busqueda": "fracciones",
        "estado_revision": "con_observaciones",
        "limit": 25,
        "offset": 50,
        # Año lectivo, fase 3 (paso 3.5b): sin año, None, que es el activo.
        "anio_lectivo_id": None,
    }


def test_admin_list_keeps_generic_500_error(monkeypatch):
    def fail(**_filters):
        raise RuntimeError("detalle interno")

    monkeypatch.setattr(plan_de_clases, "listar_planes_admin_controller", fail)

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.listar_planes_admin,
            profesor_id=None,
            fecha_desde=None,
            fecha_hasta=None,
            busqueda=None,
            estado_revision=None,
            limit=50,
            offset=0,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "No se pudieron cargar los planes de clases"


def test_admin_detail_delegates_and_preserves_controller_404(monkeypatch):
    expected = {"id": 31, "imagen1": "db/key.jpg", "imagen2": None}
    monkeypatch.setattr(
        plan_de_clases,
        "obtener_plan_admin_controller",
        lambda plan_id: expected if plan_id == 31 else pytest.fail("ID inesperado"),
    )

    response = _invoke(plan_de_clases.obtener_plan_admin, plan_id=31)

    assert response is expected

    def missing(_plan_id):
        raise HTTPException(status_code=404, detail="Plan de clases no encontrado")

    monkeypatch.setattr(plan_de_clases, "obtener_plan_admin_controller", missing)

    with pytest.raises(HTTPException) as exc_info:
        _invoke(plan_de_clases.obtener_plan_admin, plan_id=999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Plan de clases no encontrado"


def test_observations_check_ownership_then_delegate_without_transforming(monkeypatch):
    current_user = {"id": 9, "rol": "profesor"}
    expected = [{"id": 4, "plan_id": 31, "observacion": "Revisar objetivo"}]
    observed = []

    def fake_guard(plan_id, user, detail):
        observed.append(("guard", plan_id, user, detail))

    def fake_controller(plan_id):
        observed.append(("controller", plan_id))
        return expected

    monkeypatch.setattr(plan_de_clases, "require_plan_de_clases_access", fake_guard)
    monkeypatch.setattr(
        plan_de_clases,
        "listar_observaciones_plan_controller",
        fake_controller,
    )

    response = _invoke(
        plan_de_clases.listar_observaciones_plan,
        plan_id=31,
        current_user=current_user,
    )

    assert response is expected
    assert observed == [
        ("guard", 31, current_user, "No tienes permisos para este plan"),
        ("controller", 31),
    ]


def test_observations_denial_stops_before_controller(monkeypatch):
    current_user = {"id": 9, "rol": "profesor"}

    def deny(plan_id, user, detail):
        assert (plan_id, user, detail) == (
            31,
            current_user,
            "No tienes permisos para este plan",
        )
        raise HTTPException(status_code=403, detail=detail)

    monkeypatch.setattr(plan_de_clases, "require_plan_de_clases_access", deny)
    monkeypatch.setattr(
        plan_de_clases,
        "listar_observaciones_plan_controller",
        lambda *_args: pytest.fail("No debe listar observaciones"),
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.listar_observaciones_plan,
            plan_id=31,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "No tienes permisos para este plan"


def test_observations_preserve_controller_404_after_authorization(monkeypatch):
    monkeypatch.setattr(
        plan_de_clases,
        "require_plan_de_clases_access",
        lambda *_args, **_kwargs: None,
    )

    def missing(_plan_id):
        raise HTTPException(status_code=404, detail="Plan de clases no encontrado")

    monkeypatch.setattr(
        plan_de_clases,
        "listar_observaciones_plan_controller",
        missing,
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.listar_observaciones_plan,
            plan_id=999,
            current_user={"id": 1, "rol": "admin"},
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Plan de clases no encontrado"
