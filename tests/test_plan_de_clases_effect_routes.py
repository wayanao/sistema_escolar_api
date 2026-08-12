"""Caracterizacion de los seis endpoints con efectos migrados en 2.3b."""

from collections import Counter
from contextlib import contextmanager
from datetime import date
import inspect
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.routing import APIRoute
from starlette.datastructures import Headers

from app.controllers import plan_de_clases_controller
from app.dependencies import get_current_active_admin, get_current_user
from app.globals import tenant_schema_var
from app.repositories import plan_de_clases_repository
from app.routes import plan_de_clases
from app.schemas.plan_de_clases import PlanObservacionCreate, PlanRevisionUpdate


TARGET_ROUTES = {
    ("/plan-de-clases", "POST"): (
        plan_de_clases.crear_plan_de_clases,
        get_current_user,
    ),
    ("/plan-de-clases/{plan_id}/imagen", "DELETE"): (
        plan_de_clases.eliminar_imagen_plan_profesor,
        get_current_user,
    ),
    ("/admin/plan-de-clases/{plan_id}/revision", "PATCH"): (
        plan_de_clases.actualizar_revision_plan,
        get_current_active_admin,
    ),
    ("/admin/plan-de-clases/{plan_id}/observaciones", "POST"): (
        plan_de_clases.crear_observacion_plan,
        get_current_active_admin,
    ),
    ("/plan-de-clases/{plan_id}/observaciones/{observacion_id}/vista", "PATCH"): (
        plan_de_clases.marcar_observacion_vista,
        get_current_user,
    ),
    ("/admin/plan-de-clases/{plan_id}/imagen", "DELETE"): (
        plan_de_clases.eliminar_imagen_plan_admin,
        get_current_active_admin,
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


def _operation(paths, path, method):
    return paths[path][method.lower()]


def _parameter(operation, name, location):
    return next(
        parameter
        for parameter in operation["parameters"]
        if parameter["name"] == name and parameter["in"] == location
    )


def _schema_from_ref(document, schema):
    if "$ref" in schema:
        reference = schema["$ref"]
        return document["components"]["schemas"][reference.rsplit("/", 1)[-1]]
    if "allOf" in schema:
        assert len(schema["allOf"]) == 1
        return _schema_from_ref(document, schema["allOf"][0])
    return schema


def _nullable_options(schema):
    options = schema.get("anyOf") or schema.get("oneOf")
    assert options is not None
    assert any(option.get("type") == "null" for option in options)
    return [option for option in options if option.get("type") != "null"]


def _create_kwargs(**overrides):
    values = {
        "asignacion_id": 23,
        "version_esperada": 4,
        "periodo": 2,
        "unidad": "Fracciones",
        "proposito": "Resolver problemas",
        "clase": "Inicio, desarrollo y cierre",
        "estandar": "Pensamiento numerico",
        "dba": "Compara fracciones",
        "competencias": "Argumentacion",
        "actividad_casa": "Practica guiada",
        "tema": "Fracciones equivalentes",
        "fecha": "2026-08-12",
        "imagen1": object(),
        "imagen2": object(),
        "current_user": {"id": 9, "rol": "profesor", "tenant": "tenant_demo"},
    }
    values.update(overrides)
    return values


class FakeUpload:
    def __init__(self, filename, content_type, content):
        self.filename = filename
        self.content_type = content_type
        self.file = BytesIO(content)


class ScriptedCursor:
    def __init__(self, rows):
        self.rows = iter(rows)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return next(self.rows)


def test_effect_routes_preserve_paths_methods_and_dependencies():
    routes = _target_api_routes()

    assert len(routes) == len(TARGET_ROUTES) == 6
    assert {(route.path, next(iter(route.methods))) for route in routes} == set(
        TARGET_ROUTES
    )
    for route in routes:
        assert len(route.methods) == 1
        method = next(iter(route.methods))
        endpoint, dependency = TARGET_ROUTES[(route.path, method)]
        assert route.methods == {method}
        assert route.endpoint is endpoint
        assert Counter(item.call for item in route.dependant.dependencies) == Counter(
            {dependency: 1}
        )


def test_effect_registered_endpoints_are_sync():
    routes = _target_api_routes()

    assert len(routes) == len(TARGET_ROUTES) == 6
    assert all(not inspect.iscoroutinefunction(route.endpoint) for route in routes)


def test_create_route_preserves_multipart_contract():
    app = FastAPI()
    app.include_router(plan_de_clases.router)
    document = app.openapi()
    operation = _operation(document["paths"], "/plan-de-clases", "POST")
    request_body = operation["requestBody"]

    assert request_body["required"] is True
    assert set(request_body["content"]) == {"multipart/form-data"}
    schema = _schema_from_ref(
        document,
        request_body["content"]["multipart/form-data"]["schema"],
    )
    properties = schema["properties"]
    assert set(schema["required"]) == {"asignacion_id", "fecha"}
    assert properties["asignacion_id"]["type"] == "integer"
    assert properties["fecha"]["type"] == "string"
    assert _nullable_options(properties["version_esperada"]) == [
        {"type": "integer"}
    ]
    assert properties["version_esperada"].get("default") is None
    assert properties["periodo"]["default"] == 1
    for name in (
        "unidad",
        "proposito",
        "clase",
        "estandar",
        "dba",
        "competencias",
        "actividad_casa",
        "tema",
    ):
        assert properties[name]["type"] == "string"
        assert properties[name]["default"] == ""
    for name in ("imagen1", "imagen2"):
        assert name not in schema["required"]
        assert properties[name]["type"] == "string"
        assert (
            properties[name].get("contentMediaType") == "application/octet-stream"
            or properties[name].get("format") == "binary"
        )


def test_json_effect_routes_preserve_body_schemas():
    app = FastAPI()
    app.include_router(plan_de_clases.router)
    document = app.openapi()

    revision = _operation(
        document["paths"],
        "/admin/plan-de-clases/{plan_id}/revision",
        "PATCH",
    )
    revision_schema = _schema_from_ref(
        document,
        revision["requestBody"]["content"]["application/json"]["schema"],
    )
    assert revision["requestBody"]["required"] is True
    assert set(revision_schema["required"]) == {"estado", "version"}
    assert set(revision_schema["properties"]["estado"]["enum"]) == {
        "visto",
        "revisado",
    }
    assert revision_schema["properties"]["version"]["minimum"] == 1
    revision_comment = _nullable_options(
        revision_schema["properties"]["comentario"]
    )
    assert revision_comment == [{"type": "string", "maxLength": 3000}]

    observation = _operation(
        document["paths"],
        "/admin/plan-de-clases/{plan_id}/observaciones",
        "POST",
    )
    observation_schema = _schema_from_ref(
        document,
        observation["requestBody"]["content"]["application/json"]["schema"],
    )
    assert observation["requestBody"]["required"] is True
    assert set(observation_schema["required"]) == {"observacion", "version"}
    text_schema = observation_schema["properties"]["observacion"]
    assert text_schema["type"] == "string"
    assert text_schema["minLength"] == 1
    assert text_schema["maxLength"] == 3000
    assert observation_schema["properties"]["version"]["minimum"] == 1


def test_delete_and_mark_routes_preserve_path_and_slot_parameters():
    app = FastAPI()
    app.include_router(plan_de_clases.router)
    paths = app.openapi()["paths"]

    for path in (
        "/plan-de-clases/{plan_id}/imagen",
        "/admin/plan-de-clases/{plan_id}/imagen",
    ):
        operation = _operation(paths, path, "DELETE")
        plan_id = _parameter(operation, "plan_id", "path")
        slot = _parameter(operation, "slot", "query")
        assert plan_id["required"] is True
        assert plan_id["schema"]["type"] == "integer"
        assert slot["required"] is True
        assert slot["schema"]["type"] == "string"
        assert slot["schema"]["pattern"] == "^(imagen1|imagen2)$"

    mark = _operation(
        paths,
        "/plan-de-clases/{plan_id}/observaciones/{observacion_id}/vista",
        "PATCH",
    )
    for name in ("plan_id", "observacion_id"):
        parameter = _parameter(mark, name, "path")
        assert parameter["required"] is True
        assert parameter["schema"]["type"] == "integer"


def test_create_checks_access_then_builds_model_and_delegates(monkeypatch):
    values = _create_kwargs()
    expected = {"id": 31, "version_revision": 5, "estado_revision": "pendiente"}
    observed = []

    def fake_guard(asignacion_id, user, detail):
        observed.append(("guard", asignacion_id, user, detail))

    def fake_controller(model, imagen1, imagen2):
        observed.append(("controller", model, imagen1, imagen2))
        return expected

    monkeypatch.setattr(plan_de_clases, "require_asignacion_access", fake_guard)
    monkeypatch.setattr(
        plan_de_clases,
        "crear_plan_de_clases_controller",
        fake_controller,
    )

    response = _invoke(plan_de_clases.crear_plan_de_clases, **values)

    assert response is expected
    assert observed[0] == (
        "guard",
        23,
        values["current_user"],
        "No tienes permisos para esta asignación",
    )
    _label, model, imagen1, imagen2 = observed[1]
    assert model.model_dump() == {
        "asignacion_id": 23,
        "version_esperada": 4,
        "periodo": 2,
        "unidad": "Fracciones",
        "proposito": "Resolver problemas",
        "clase": "Inicio, desarrollo y cierre",
        "estandar": "Pensamiento numerico",
        "dba": "Compara fracciones",
        "competencias": "Argumentacion",
        "actividad_casa": "Practica guiada",
        "tema": "Fracciones equivalentes",
        "fecha": date(2026, 8, 12),
    }
    assert imagen1 is values["imagen1"]
    assert imagen2 is values["imagen2"]


def test_create_access_denial_precedes_validation_and_controller(monkeypatch):
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
        "crear_plan_de_clases_controller",
        lambda *_args: pytest.fail("No debe crear el plan"),
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.crear_plan_de_clases,
            **_create_kwargs(fecha="fecha-invalida", current_user=current_user),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "No tienes permisos para esta asignación"


@pytest.mark.parametrize(
    ("overrides", "detail_fragment"),
    [
        ({"fecha": "fecha-invalida"}, "Invalid isoformat string"),
        ({"version_esperada": -1}, "version_esperada"),
    ],
)
def test_create_validation_errors_remain_400(monkeypatch, overrides, detail_fragment):
    monkeypatch.setattr(
        plan_de_clases,
        "require_asignacion_access",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        plan_de_clases,
        "crear_plan_de_clases_controller",
        lambda *_args: pytest.fail("No debe llegar al controller"),
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.crear_plan_de_clases,
            **_create_kwargs(**overrides),
        )

    assert exc_info.value.status_code == 400
    assert detail_fragment in exc_info.value.detail


@pytest.mark.parametrize(
    ("error", "status_code", "detail"),
    [
        (
            HTTPException(
                status_code=409,
                detail={"mensaje": "Conflicto", "version_actual": 7},
            ),
            409,
            {"mensaje": "Conflicto", "version_actual": 7},
        ),
        (RuntimeError("storage no disponible"), 400, "storage no disponible"),
    ],
)
def test_create_preserves_http_errors_and_translates_other_errors(
    monkeypatch, error, status_code, detail
):
    monkeypatch.setattr(
        plan_de_clases,
        "require_asignacion_access",
        lambda *_args, **_kwargs: None,
    )

    def fail(*_args):
        raise error

    monkeypatch.setattr(plan_de_clases, "crear_plan_de_clases_controller", fail)

    with pytest.raises(HTTPException) as exc_info:
        _invoke(plan_de_clases.crear_plan_de_clases, **_create_kwargs())

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


@pytest.mark.parametrize(
    ("handler_name", "slot", "expected_args", "expected_kwargs"),
    [
        (
            "eliminar_imagen_plan_profesor",
            "imagen1",
            (31, "imagen1"),
            {"reiniciar_revision": True},
        ),
        (
            "eliminar_imagen_plan_admin",
            "imagen2",
            (31, "imagen2"),
            {},
        ),
    ],
)
def test_delete_routes_preserve_mode_and_response(
    monkeypatch, handler_name, slot, expected_args, expected_kwargs
):
    current_user = {"id": 9, "rol": "profesor"}
    expected = {"mensaje": "Imagen eliminada correctamente"}
    observed = []

    def fake_guard(plan_id, user, detail):
        observed.append(("guard", plan_id, user, detail))

    def fake_controller(*args, **kwargs):
        observed.append(("controller", args, kwargs))
        return expected

    monkeypatch.setattr(plan_de_clases, "require_plan_de_clases_access", fake_guard)
    monkeypatch.setattr(
        plan_de_clases,
        "eliminar_imagen_plan_admin_controller",
        fake_controller,
    )
    handler = getattr(plan_de_clases, handler_name)
    kwargs = {"plan_id": 31, "slot": slot}
    if handler_name.endswith("profesor"):
        kwargs["current_user"] = current_user

    response = _invoke(handler, **kwargs)

    assert response is expected
    assert observed[-1] == ("controller", expected_args, expected_kwargs)
    if handler_name.endswith("profesor"):
        assert observed[0] == (
            "guard",
            31,
            current_user,
            "No tienes permisos para este plan",
        )
    else:
        assert observed == [("controller", expected_args, expected_kwargs)]


def test_professor_delete_denial_stops_before_effect(monkeypatch):
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
        "eliminar_imagen_plan_admin_controller",
        lambda *_args, **_kwargs: pytest.fail("No debe eliminar la imagen"),
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.eliminar_imagen_plan_profesor,
            plan_id=31,
            slot="imagen1",
            current_user=current_user,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "No tienes permisos para este plan"


@pytest.mark.parametrize(
    ("handler_name", "error", "status_code", "detail"),
    [
        (
            "eliminar_imagen_plan_profesor",
            HTTPException(status_code=404, detail="Plan de clases no encontrado"),
            404,
            "Plan de clases no encontrado",
        ),
        (
            "eliminar_imagen_plan_admin",
            HTTPException(status_code=404, detail="Plan de clases no encontrado"),
            404,
            "Plan de clases no encontrado",
        ),
        (
            "eliminar_imagen_plan_profesor",
            RuntimeError("fallo interno"),
            500,
            "No se pudo eliminar la imagen",
        ),
        (
            "eliminar_imagen_plan_admin",
            RuntimeError("fallo interno"),
            500,
            "No se pudo eliminar la imagen",
        ),
    ],
)
def test_delete_routes_preserve_error_translation(
    monkeypatch, handler_name, error, status_code, detail
):
    monkeypatch.setattr(
        plan_de_clases,
        "require_plan_de_clases_access",
        lambda *_args, **_kwargs: None,
    )

    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(
        plan_de_clases,
        "eliminar_imagen_plan_admin_controller",
        fail,
    )
    handler = getattr(plan_de_clases, handler_name)
    kwargs = {"plan_id": 31, "slot": "imagen1"}
    if handler_name.endswith("profesor"):
        kwargs["current_user"] = {"id": 9, "rol": "profesor"}

    with pytest.raises(HTTPException) as exc_info:
        _invoke(handler, **kwargs)

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


@pytest.mark.parametrize(
    ("handler_name", "controller_name", "data"),
    [
        (
            "actualizar_revision_plan",
            "actualizar_revision_plan_controller",
            PlanRevisionUpdate(estado="revisado", version=4, comentario="Bien"),
        ),
        (
            "crear_observacion_plan",
            "crear_observacion_plan_controller",
            PlanObservacionCreate(observacion="Reforzar el cierre", version=4),
        ),
    ],
)
def test_admin_effect_routes_delegate_authenticated_admin(
    monkeypatch, handler_name, controller_name, data
):
    expected = {"resultado": "ok"}
    observed = []

    def fake_controller(*args):
        observed.append(args)
        return expected

    monkeypatch.setattr(plan_de_clases, controller_name, fake_controller)

    response = _invoke(
        getattr(plan_de_clases, handler_name),
        plan_id=31,
        data=data,
        current_user={"id": 8, "rol": "admin"},
    )

    assert response is expected
    assert observed == [(31, data, 8)]


@pytest.mark.parametrize(
    ("handler_name", "controller_name", "status_code"),
    [
        ("actualizar_revision_plan", "actualizar_revision_plan_controller", 409),
        ("crear_observacion_plan", "crear_observacion_plan_controller", 404),
    ],
)
def test_admin_effect_routes_preserve_controller_http_errors(
    monkeypatch, handler_name, controller_name, status_code
):
    data = (
        PlanRevisionUpdate(estado="visto", version=4)
        if handler_name == "actualizar_revision_plan"
        else PlanObservacionCreate(observacion="Revisar", version=4)
    )
    detail = {"version_actual": 5} if status_code == 409 else "No encontrado"

    def fail(*_args):
        raise HTTPException(status_code=status_code, detail=detail)

    monkeypatch.setattr(plan_de_clases, controller_name, fail)

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            getattr(plan_de_clases, handler_name),
            plan_id=31,
            data=data,
            current_user={"id": 8, "rol": "admin"},
        )

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


def test_mark_view_rejects_non_professor_before_guard_and_controller(monkeypatch):
    monkeypatch.setattr(
        plan_de_clases,
        "require_plan_de_clases_access",
        lambda *_args, **_kwargs: pytest.fail("No debe comprobar ownership"),
    )
    monkeypatch.setattr(
        plan_de_clases,
        "marcar_observacion_vista_controller",
        lambda *_args: pytest.fail("No debe marcar la observacion"),
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.marcar_observacion_vista,
            plan_id=31,
            observacion_id=7,
            current_user={"id": 8, "rol": "admin"},
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Accion exclusiva para profesores"


def test_mark_view_denial_stops_before_controller(monkeypatch):
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
        "marcar_observacion_vista_controller",
        lambda *_args: pytest.fail("No debe marcar la observacion"),
    )

    with pytest.raises(HTTPException) as exc_info:
        _invoke(
            plan_de_clases.marcar_observacion_vista,
            plan_id=31,
            observacion_id=7,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "No tienes permisos para este plan"


@pytest.mark.parametrize("missing", [False, True])
def test_mark_view_delegates_or_preserves_404(monkeypatch, missing):
    current_user = {"id": 9, "rol": "profesor"}
    expected = {"id": 7, "vista_por_profesor_at": "ahora"}
    observed = []

    def fake_guard(plan_id, user, detail):
        observed.append(("guard", plan_id, user, detail))

    def fake_controller(plan_id, observation_id):
        observed.append(("controller", plan_id, observation_id))
        if missing:
            raise HTTPException(
                status_code=404,
                detail="Observacion no encontrada para este plan",
            )
        return expected

    monkeypatch.setattr(plan_de_clases, "require_plan_de_clases_access", fake_guard)
    monkeypatch.setattr(
        plan_de_clases,
        "marcar_observacion_vista_controller",
        fake_controller,
    )

    if missing:
        with pytest.raises(HTTPException) as exc_info:
            _invoke(
                plan_de_clases.marcar_observacion_vista,
                plan_id=31,
                observacion_id=7,
                current_user=current_user,
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Observacion no encontrada para este plan"
    else:
        response = _invoke(
            plan_de_clases.marcar_observacion_vista,
            plan_id=31,
            observacion_id=7,
            current_user=current_user,
        )
        assert response is expected
    assert observed == [
        ("guard", 31, current_user, "No tienes permisos para este plan"),
        ("controller", 31, 7),
    ]


def test_storage_directory_uses_current_tenant():
    token = tenant_schema_var.set("tenant_demo")
    try:
        assert (
            plan_de_clases_controller.obtener_directorio_archivos()
            == "tenant_demo/plan_de_clases"
        )
    finally:
        tenant_schema_var.reset(token)


def test_valid_image_is_read_and_saved_under_tenant_directory(monkeypatch):
    upload = UploadFile(
        BytesIO(b"contenido"),
        filename="evidencia.JPG",
        headers=Headers({"content-type": "image/jpeg"}),
    )
    observed = {}
    monkeypatch.setattr(
        plan_de_clases_controller.uuid,
        "uuid4",
        lambda: SimpleNamespace(hex="archivo123"),
    )

    def fake_save(key, content, content_type):
        observed.update(
            key=key,
            content=content,
            content_type=content_type,
        )

    monkeypatch.setattr(plan_de_clases_controller, "save_bytes", fake_save)
    monkeypatch.setattr(
        plan_de_clases_controller,
        "db_path_for_key",
        lambda key: f"uploads/{key}",
    )

    result = plan_de_clases_controller.guardar_imagen_plan(
        "tenant_demo/plan_de_clases",
        upload,
    )

    assert result == "uploads/tenant_demo/plan_de_clases/archivo123.jpg"
    assert observed == {
        "key": "tenant_demo/plan_de_clases/archivo123.jpg",
        "content": b"contenido",
        "content_type": "image/jpeg",
    }


@pytest.mark.parametrize(
    ("upload", "detail"),
    [
        (
            FakeUpload("evidencia.jpg", "text/plain", b"contenido"),
            "Tipo de imagen no permitido",
        ),
        (
            FakeUpload("evidencia.gif", "image/png", b"contenido"),
            "Extension de imagen no permitida",
        ),
        (
            FakeUpload(
                "evidencia.png",
                "image/png",
                b"x" * (plan_de_clases_controller.MAX_IMAGE_BYTES + 1),
            ),
            "Imagen demasiado grande (max 5MB)",
        ),
    ],
)
def test_invalid_images_fail_before_storage(monkeypatch, upload, detail):
    monkeypatch.setattr(
        plan_de_clases_controller,
        "save_bytes",
        lambda *_args, **_kwargs: pytest.fail("No debe escribir storage"),
    )

    with pytest.raises(HTTPException) as exc_info:
        plan_de_clases_controller.guardar_imagen_plan(
            "tenant_demo/plan_de_clases",
            upload,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == detail


def test_create_controller_preserves_image_then_db_order(monkeypatch):
    first = object()
    second = object()
    expected = {"id": 31, "estado_revision": "pendiente"}
    events = []
    paths = {first: "uploads/tenant/first.jpg", second: "uploads/tenant/second.jpg"}

    monkeypatch.setattr(
        plan_de_clases_controller,
        "obtener_directorio_archivos",
        lambda: "tenant/plan_de_clases",
    )

    def fake_image(directory, image):
        events.append(("image", directory, image))
        return paths[image]

    def fake_plan(model, image1_path, image2_path):
        events.append(("db", model, image1_path, image2_path))
        return expected

    monkeypatch.setattr(plan_de_clases_controller, "guardar_imagen_plan", fake_image)
    monkeypatch.setattr(plan_de_clases_controller, "guardar_plan", fake_plan)
    monkeypatch.setattr(
        plan_de_clases_controller,
        "delete_file",
        lambda _path: pytest.fail("No debe limpiar en éxito"),
    )
    model = SimpleNamespace()

    result = plan_de_clases_controller.crear_plan_de_clases_controller(
        model,
        first,
        second,
    )

    assert result is expected
    assert events == [
        ("image", "tenant/plan_de_clases", first),
        ("image", "tenant/plan_de_clases", second),
        (
            "db",
            model,
            "uploads/tenant/first.jpg",
            "uploads/tenant/second.jpg",
        ),
    ]


def test_create_controller_keeps_canonical_version_conflict(monkeypatch):
    monkeypatch.setattr(
        plan_de_clases_controller,
        "obtener_directorio_archivos",
        lambda: "tenant/plan_de_clases",
    )
    monkeypatch.setattr(
        plan_de_clases_controller,
        "guardar_plan",
        lambda *_args: {
            "resultado": "version_desactualizada",
            "version_actual": 7,
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        plan_de_clases_controller.crear_plan_de_clases_controller(
            SimpleNamespace(),
            imagen1=None,
            imagen2=None,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "mensaje": (
            "Este plan fue actualizado en otra pestaña o dispositivo. "
            "Carga la versión más reciente antes de guardar."
        ),
        "version_actual": 7,
    }


@pytest.mark.parametrize(
    ("result", "status_code", "detail"),
    [
        (
            {"resultado": "no_encontrado"},
            404,
            "Plan de clases no encontrado",
        ),
        (
            {"resultado": "version_desactualizada", "version_actual": 7},
            409,
            {
                "mensaje": "El plan fue actualizado. Recarga antes de continuar.",
                "version_actual": 7,
            },
        ),
    ],
)
def test_revision_result_keeps_canonical_http_details(result, status_code, detail):
    with pytest.raises(HTTPException) as exc_info:
        plan_de_clases_controller._resolver_resultado_revision(result)

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


def test_create_controller_cleans_first_image_if_second_save_fails(monkeypatch):
    first = object()
    second = object()
    events = []

    monkeypatch.setattr(
        plan_de_clases_controller,
        "obtener_directorio_archivos",
        lambda: "tenant/plan_de_clases",
    )

    def fake_image(_directory, image):
        events.append(("image", image))
        if image is second:
            raise RuntimeError("segundo archivo falló")
        return "uploads/tenant/first.jpg"

    monkeypatch.setattr(plan_de_clases_controller, "guardar_imagen_plan", fake_image)
    monkeypatch.setattr(
        plan_de_clases_controller,
        "guardar_plan",
        lambda *_args: pytest.fail("No debe tocar DB"),
    )
    monkeypatch.setattr(
        plan_de_clases_controller,
        "delete_file",
        lambda path: events.append(("delete", path)),
    )

    with pytest.raises(RuntimeError, match="segundo archivo falló"):
        plan_de_clases_controller.crear_plan_de_clases_controller(
            SimpleNamespace(),
            first,
            second,
        )

    assert events == [
        ("image", first),
        ("image", second),
        ("delete", "uploads/tenant/first.jpg"),
    ]


@pytest.mark.parametrize("missing", [False, True])
def test_delete_controller_calls_repository_before_storage_delete(
    monkeypatch, missing
):
    events = []

    def fake_repository(plan_id, slot, reiniciar_revision=False):
        events.append(("db", plan_id, slot, reiniciar_revision))
        return None if missing else "uploads/tenant/plan.jpg"

    monkeypatch.setattr(
        plan_de_clases_controller,
        "eliminar_imagen_plan_admin",
        fake_repository,
    )
    monkeypatch.setattr(
        plan_de_clases_controller,
        "delete_file",
        lambda path: events.append(("delete", path)),
    )

    if missing:
        with pytest.raises(HTTPException) as exc_info:
            plan_de_clases_controller.eliminar_imagen_plan_admin_controller(
                31,
                "imagen1",
                reiniciar_revision=True,
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Plan de clases no encontrado"
        assert events == [("db", 31, "imagen1", True)]
    else:
        result = plan_de_clases_controller.eliminar_imagen_plan_admin_controller(
            31,
            "imagen1",
            reiniciar_revision=True,
        )
        assert result == {"mensaje": "Imagen eliminada correctamente"}
        assert events == [
            ("db", 31, "imagen1", True),
            ("delete", "uploads/tenant/plan.jpg"),
        ]


def test_admin_delete_repository_keeps_simple_transaction(monkeypatch):
    cursor = ScriptedCursor([("uploads/tenant/plan.jpg", "revisado")])

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)

    path = plan_de_clases_repository.eliminar_imagen_plan(
        31,
        "imagen2",
        reiniciar_revision=False,
    )

    assert path == "uploads/tenant/plan.jpg"
    assert len(cursor.calls) == 2
    assert "SELECT imagen2, estado_revision" in cursor.calls[0][0]
    assert "FOR UPDATE" in cursor.calls[0][0]
    assert cursor.calls[0][1] == (31,)
    update, params = cursor.calls[1]
    assert "SET imagen2 = NULL" in update
    assert "version_revision" not in update
    assert "plan_de_clases_notificaciones_admin" not in update
    assert params == (31,)


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ((7, "ahora"), {"id": 7, "vista_por_profesor_at": "ahora"}),
        (None, None),
    ],
)
def test_mark_view_repository_preserves_transaction_and_result(
    monkeypatch, row, expected
):
    cursor = ScriptedCursor([row])

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)

    result = plan_de_clases_repository.marcar_observacion_vista(31, 7)

    assert result == expected
    assert len(cursor.calls) == 1
    query, params = cursor.calls[0]
    assert "COALESCE" in query
    assert "WHERE id = %s AND plan_id = %s" in query
    assert params == (7, 31)


def test_mark_view_controller_keeps_missing_404(monkeypatch):
    monkeypatch.setattr(
        plan_de_clases_controller,
        "confirmar_observacion_vista",
        lambda _plan_id, _observation_id: None,
    )

    with pytest.raises(HTTPException) as exc_info:
        plan_de_clases_controller.marcar_observacion_vista_controller(31, 7)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Observacion no encontrada para este plan"
