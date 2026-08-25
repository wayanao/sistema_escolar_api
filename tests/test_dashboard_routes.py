import inspect
from collections import Counter

import pytest
from fastapi import FastAPI, HTTPException

from app.routes import dashboard


ADMIN = {"id": 1, "rol": "admin", "tenant": "tenant_demo"}
PROFESOR = {"id": 7, "rol": "profesor", "tenant": "tenant_demo"}


ROUTE_CASES = [
    pytest.param(
        dashboard.obtener_cumpleanos_admin,
        "obtener_cumpleanos_admin_controller",
        (),
        {"dias": 11, "_admin": ADMIN},
        (),
        {"dias": 11},
        id="cumpleanos-admin",
    ),
    pytest.param(
        dashboard.obtener_cumpleanos_profesor,
        "obtener_cumpleanos_profesor_controller",
        (7,),
        {"dias": 9, "current_user": PROFESOR},
        (7,),
        {"dias": 9},
        id="cumpleanos-profesor",
    ),
    pytest.param(
        dashboard.obtener_inasistencias_profesor,
        "obtener_inasistencias_profesor_controller",
        (7,),
        {"current_user": PROFESOR},
        (7,),
        {},
        id="inasistencias",
    ),
    pytest.param(
        dashboard.obtener_notas_bajas_profesor,
        "obtener_notas_bajas_profesor_controller",
        (7,),
        {"curso_id": 4, "asignacion_id": 12, "current_user": PROFESOR},
        (7,),
        {"curso_id": 4, "asignacion_id": 12},
        id="notas-bajas",
    ),
    pytest.param(
        dashboard.obtener_notas_altas_profesor,
        "obtener_notas_altas_profesor_controller",
        (7,),
        {"curso_id": 4, "asignacion_id": None, "current_user": PROFESOR},
        (7,),
        {"curso_id": 4, "asignacion_id": None},
        id="notas-altas",
    ),
    pytest.param(
        dashboard.obtener_ranking_rendimiento,
        "obtener_ranking_rendimiento_controller",
        (12,),
        {"periodo": 2, "current_user": PROFESOR},
        (12, 2),
        {},
        id="ranking-bajo",
    ),
    pytest.param(
        dashboard.obtener_ranking_mejor_rendimiento,
        "obtener_ranking_mejor_rendimiento_controller",
        (12,),
        {"periodo": 2, "current_user": PROFESOR},
        (12, 2),
        {},
        id="ranking-alto",
    ),
]


def _invoke(route, args, kwargs):
    return route(*args, **kwargs)


def _allow_route_guards(monkeypatch):
    monkeypatch.setattr(dashboard, "require_profesor_scope", lambda *_a, **_k: None)
    monkeypatch.setattr(dashboard, "require_asignacion_access", lambda *_a, **_k: None)
    monkeypatch.setattr(
        dashboard,
        "validar_filtro_rendimiento_profesor",
        lambda *_a, **_k: None,
    )


@pytest.mark.parametrize(
    ("route", "controller_name", "route_args", "route_kwargs", "expected_args", "expected_kwargs"),
    ROUTE_CASES,
)
def test_dashboard_routes_delegate_without_transforming_response(
    monkeypatch,
    route,
    controller_name,
    route_args,
    route_kwargs,
    expected_args,
    expected_kwargs,
):
    expected = [{"marker": controller_name}]
    calls = []

    def fake_controller(*args, **kwargs):
        calls.append((args, kwargs))
        return expected

    _allow_route_guards(monkeypatch)
    monkeypatch.setattr(dashboard, controller_name, fake_controller)

    response = _invoke(route, route_args, route_kwargs)

    assert response is expected
    assert calls == [(expected_args, expected_kwargs)]


@pytest.mark.parametrize(
    ("route", "controller_name", "route_args", "route_kwargs", "_expected_args", "_expected_kwargs"),
    ROUTE_CASES,
)
def test_dashboard_routes_translate_controller_errors_to_400(
    monkeypatch,
    route,
    controller_name,
    route_args,
    route_kwargs,
    _expected_args,
    _expected_kwargs,
):
    def fail_controller(*_args, **_kwargs):
        raise ValueError("fallo-controlado")

    _allow_route_guards(monkeypatch)
    monkeypatch.setattr(dashboard, controller_name, fail_controller)

    with pytest.raises(HTTPException) as exc:
        _invoke(route, route_args, route_kwargs)

    assert exc.value.status_code == 400
    assert exc.value.detail == "fallo-controlado"


@pytest.mark.parametrize(
    ("route", "controller_name", "route_kwargs"),
    [
        pytest.param(
            dashboard.obtener_cumpleanos_profesor,
            "obtener_cumpleanos_profesor_controller",
            {"dias": 9, "current_user": PROFESOR},
            id="cumpleanos",
        ),
        pytest.param(
            dashboard.obtener_inasistencias_profesor,
            "obtener_inasistencias_profesor_controller",
            {"current_user": PROFESOR},
            id="inasistencias",
        ),
        pytest.param(
            dashboard.obtener_notas_bajas_profesor,
            "obtener_notas_bajas_profesor_controller",
            {"curso_id": 4, "asignacion_id": 12, "current_user": PROFESOR},
            id="notas-bajas",
        ),
        pytest.param(
            dashboard.obtener_notas_altas_profesor,
            "obtener_notas_altas_profesor_controller",
            {"curso_id": 4, "asignacion_id": 12, "current_user": PROFESOR},
            id="notas-altas",
        ),
    ],
)
def test_profesor_scope_errors_stay_outside_controller_error_translation(
    monkeypatch,
    route,
    controller_name,
    route_kwargs,
):
    calls = []

    def deny(profesor_id, current_user, detail):
        calls.append((profesor_id, current_user, detail))
        raise HTTPException(status_code=403, detail=detail)

    monkeypatch.setattr(dashboard, "require_profesor_scope", deny)
    monkeypatch.setattr(
        dashboard,
        "validar_filtro_rendimiento_profesor",
        lambda *_a, **_k: pytest.fail("el filtro no debe ejecutarse tras denegar scope"),
    )
    monkeypatch.setattr(
        dashboard,
        controller_name,
        lambda *_a, **_k: pytest.fail("el controller no debe ejecutarse"),
    )

    with pytest.raises(HTTPException) as exc:
        _invoke(route, (7,), route_kwargs)

    assert exc.value.status_code == 403
    assert exc.value.detail == "No tienes permisos para consultar datos de otro profesor"
    assert calls == [(7, PROFESOR, exc.value.detail)]


@pytest.mark.parametrize(
    ("route", "controller_name"),
    [
        (dashboard.obtener_ranking_rendimiento, "obtener_ranking_rendimiento_controller"),
        (
            dashboard.obtener_ranking_mejor_rendimiento,
            "obtener_ranking_mejor_rendimiento_controller",
        ),
    ],
)
def test_asignacion_access_errors_stay_outside_controller_error_translation(
    monkeypatch,
    route,
    controller_name,
):
    calls = []

    def deny(asignacion_id, current_user, detail):
        calls.append((asignacion_id, current_user, detail))
        raise HTTPException(status_code=403, detail=detail)

    monkeypatch.setattr(dashboard, "require_asignacion_access", deny)
    monkeypatch.setattr(
        dashboard,
        controller_name,
        lambda *_a, **_k: pytest.fail("el controller no debe ejecutarse"),
    )

    with pytest.raises(HTTPException) as exc:
        _invoke(route, (12,), {"periodo": 2, "current_user": PROFESOR})

    assert exc.value.status_code == 403
    assert exc.value.detail == "No tienes permisos para consultar esta asignación"
    assert calls == [(12, PROFESOR, exc.value.detail)]


def test_performance_filter_requires_course_before_db_checks(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "validar_filtro_rendimiento_profesor_controller",
        lambda *_a: pytest.fail("no debe consultar sin curso"),
    )

    with pytest.raises(HTTPException) as exc:
        dashboard.validar_filtro_rendimiento_profesor(7, None, None, PROFESOR)

    assert exc.value.status_code == 422
    assert exc.value.detail == "Debes seleccionar un curso para consultar rendimiento"


def test_performance_filter_rejects_course_outside_profesor_scope(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "validar_filtro_rendimiento_profesor_controller",
        lambda *_a: (False, None),
    )

    with pytest.raises(HTTPException) as exc:
        dashboard.validar_filtro_rendimiento_profesor(7, 4, 12, PROFESOR)

    assert exc.value.status_code == 403
    assert exc.value.detail == "No tienes permisos para consultar este curso"


def test_performance_filter_accepts_course_without_assignment(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "validar_filtro_rendimiento_profesor_controller",
        lambda *_a: (True, None),
    )

    dashboard.validar_filtro_rendimiento_profesor(7, 4, None, PROFESOR)


def test_performance_filter_preserves_assignment_access_error(monkeypatch):
    def deny(*_args):
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para consultar esta asignación",
        )

    monkeypatch.setattr(
        dashboard,
        "validar_filtro_rendimiento_profesor_controller",
        deny,
    )

    with pytest.raises(HTTPException) as exc:
        dashboard.validar_filtro_rendimiento_profesor(7, 4, 12, PROFESOR)

    assert exc.value.status_code == 403
    assert exc.value.detail == "No tienes permisos para consultar esta asignación"


@pytest.mark.parametrize(
    ("route", "controller_name"),
    [
        (dashboard.obtener_notas_bajas_profesor, "obtener_notas_bajas_profesor_controller"),
        (dashboard.obtener_notas_altas_profesor, "obtener_notas_altas_profesor_controller"),
    ],
)
def test_performance_filter_infrastructure_errors_stay_outside_controller_translation(
    monkeypatch,
    route,
    controller_name,
):
    def fail_filter(*_args):
        raise RuntimeError("fallo-infraestructura")

    monkeypatch.setattr(dashboard, "require_profesor_scope", lambda *_a, **_k: None)
    monkeypatch.setattr(
        dashboard,
        "validar_filtro_rendimiento_profesor_controller",
        fail_filter,
    )
    monkeypatch.setattr(
        dashboard,
        controller_name,
        lambda *_a, **_k: pytest.fail("el controller final no debe ejecutarse"),
    )

    with pytest.raises(RuntimeError, match="fallo-infraestructura"):
        route(7, curso_id=4, asignacion_id=12, current_user=PROFESOR)


def test_performance_filter_rejects_assignment_from_another_course(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "validar_filtro_rendimiento_profesor_controller",
        lambda *_a: (True, False),
    )

    with pytest.raises(HTTPException) as exc:
        dashboard.validar_filtro_rendimiento_profesor(7, 4, 12, PROFESOR)

    assert exc.value.status_code == 403
    assert exc.value.detail == "La asignación no pertenece al curso seleccionado"


def test_performance_filter_passes_exact_scope_to_consolidated_check(monkeypatch):
    calls = []
    monkeypatch.setattr(
        dashboard,
        "validar_filtro_rendimiento_profesor_controller",
        lambda profesor_id, curso_id, asignacion_id, current_user: calls.append(
            (profesor_id, curso_id, asignacion_id, current_user)
        )
        or (True, True),
    )

    dashboard.validar_filtro_rendimiento_profesor(7, 4, 12, PROFESOR)

    assert calls == [(7, 4, 12, PROFESOR)]


def test_dashboard_router_preserves_paths_methods_and_dependencies():
    expected_dependencies = {
        "/dashboard/cumpleanos/admin": Counter({
            dashboard.get_current_user: 1,
            dashboard.get_current_active_admin: 1,
        }),
        "/dashboard/cumpleanos/profesor/{profesor_id}": Counter({dashboard.get_current_user: 2}),
        "/dashboard/inasistencias/{profesor_id}": Counter({dashboard.get_current_user: 2}),
        "/dashboard/notas-bajas/{profesor_id}": Counter({dashboard.get_current_user: 2}),
        "/dashboard/notas-altas/{profesor_id}": Counter({dashboard.get_current_user: 2}),
        "/dashboard/ranking/{asignacion_id}/{periodo}": Counter({dashboard.get_current_user: 2}),
        "/dashboard/ranking-mejor/{asignacion_id}/{periodo}": Counter({dashboard.get_current_user: 2}),
    }
    routes = {route.path: route for route in dashboard.router.routes}

    assert set(routes) == set(expected_dependencies)
    for path, dependency_names in expected_dependencies.items():
        route = routes[path]
        assert route.methods == {"GET"}
        assert Counter(dependency.call for dependency in route.dependant.dependencies) == (
            dependency_names
        )


def test_dashboard_openapi_preserves_query_and_path_parameters():
    app = FastAPI()
    app.include_router(dashboard.router)
    paths = app.openapi()["paths"]

    admin_parameters = {
        item["name"]: item
        for item in paths["/dashboard/cumpleanos/admin"]["get"]["parameters"]
    }
    assert admin_parameters["dias"]["in"] == "query"
    assert admin_parameters["dias"]["required"] is False
    dias_schema = admin_parameters["dias"]["schema"]
    assert dias_schema["type"] == "integer"
    assert dias_schema["minimum"] == 0
    assert dias_schema["maximum"] == 31
    assert dias_schema["default"] == 7

    notes_parameters = {
        item["name"]: item
        for item in paths["/dashboard/notas-bajas/{profesor_id}"]["get"]["parameters"]
    }
    assert (notes_parameters["profesor_id"]["in"], notes_parameters["profesor_id"]["required"]) == (
        "path",
        True,
    )
    assert (notes_parameters["curso_id"]["in"], notes_parameters["curso_id"]["required"]) == (
        "query",
        False,
    )
    assert (
        notes_parameters["asignacion_id"]["in"],
        notes_parameters["asignacion_id"]["required"],
    ) == ("query", False)

    ranking_parameters = {
        item["name"]: item
        for item in paths["/dashboard/ranking/{asignacion_id}/{periodo}"]["get"]["parameters"]
    }
    assert (ranking_parameters["asignacion_id"]["in"], ranking_parameters["asignacion_id"]["required"]) == (
        "path",
        True,
    )
    assert (ranking_parameters["periodo"]["in"], ranking_parameters["periodo"]["required"]) == (
        "path",
        True,
    )


def test_dashboard_routes_are_sync_for_fastapi_threadpool():
    routes = list(dashboard.router.routes)

    assert len(routes) == 7
    assert all(not inspect.iscoroutinefunction(route.endpoint) for route in routes)
