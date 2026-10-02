"""Caracterizacion de frontera y linea base del dominio plan_de_clases."""

import ast
import asyncio
from contextlib import contextmanager
from datetime import date, datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.core import permissions
from app.dependencies import get_current_active_admin, get_current_user
from app.repositories import plan_de_clases_repository
from app.routes import plan_de_clases
from app.schemas.plan_de_clases import PlanDeClasesCreate, PlanDeClasesResponse


ROOT = Path(__file__).resolve().parents[1]
DOMAIN_FILES = {
    "app/routes/plan_de_clases.py",
    "app/controllers/plan_de_clases_controller.py",
    "app/services/plan_de_clases_service.py",
    "app/repositories/plan_de_clases_repository.py",
    "app/schemas/plan_de_clases.py",
}
EXPECTED_ROUTES = {
    ("GET", "/notificaciones/planeadores"),
    ("POST", "/plan-de-clases"),
    ("GET", "/plan-de-clases/{asignacion_id}"),
    ("DELETE", "/plan-de-clases/{plan_id}/imagen"),
    ("GET", "/admin/plan-de-clases"),
    ("GET", "/admin/plan-de-clases/{plan_id}"),
    ("PATCH", "/admin/plan-de-clases/{plan_id}/revision"),
    ("POST", "/admin/plan-de-clases/{plan_id}/observaciones"),
    ("GET", "/plan-de-clases/{plan_id}/observaciones"),
    (
        "PATCH",
        "/plan-de-clases/{plan_id}/observaciones/{observacion_id}/vista",
    ),
    ("DELETE", "/admin/plan-de-clases/{plan_id}/imagen"),
}
PLAN_ACCESS_SQL = (
    "\n"
    "            SELECT 1\n"
    "            FROM plan_de_clases pdc\n"
    "            JOIN asignaciones a ON pdc.asignacion_id = a.id\n"
    "            WHERE pdc.id = %s AND a.profesor_id = %s\n"
    "            "
)
PLAN_IMAGE_ACCESS_SQL = (
    "\n"
    "                SELECT 1\n"
    "                FROM plan_de_clases pdc\n"
    "                JOIN asignaciones a ON a.id = pdc.asignacion_id\n"
    "                WHERE (pdc.imagen1 = %s OR pdc.imagen2 = %s)\n"
    "                  AND a.profesor_id = %s\n"
    "                "
)


def _source(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _tree(relative_path):
    return ast.parse(_source(relative_path))


def _function_source(relative_path, function_name):
    source = _source(relative_path)
    tree = ast.parse(source)
    node = next(
        item
        for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == function_name
    )
    return ast.get_source_segment(source, node)


def _execute_calls(node):
    return [
        call
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "execute"
    ]


def _asgi_request(app, method, target, body=b"", headers=None):
    async def request():
        parsed = urlsplit(target)
        sent = []
        received = False

        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": body, "more_body": False}
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}

        async def send(message):
            sent.append(message)

        encoded_headers = [(b"host", b"testserver")]
        for name, value in (headers or {}).items():
            encoded_headers.append((name.lower().encode(), value.encode()))
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": parsed.path,
            "raw_path": parsed.path.encode(),
            "query_string": parsed.query.encode(),
            "headers": encoded_headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "root_path": "",
        }
        await app(scope, receive, send)
        status_code = next(
            message["status"]
            for message in sent
            if message["type"] == "http.response.start"
        )
        response_body = b"".join(
            message.get("body", b"")
            for message in sent
            if message["type"] == "http.response.body"
        )
        return status_code, json.loads(response_body or b"null")

    return asyncio.run(request())


def _app_with_user(user):
    app = FastAPI()
    app.include_router(plan_de_clases.router)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_active_admin] = lambda: user
    return app


class PermissionCursor:
    def __init__(self, events):
        self.events = events

    def execute(self, query, params=None):
        self.events.append(("permission_query", query, params))

    def fetchone(self):
        return (1,)

    def close(self):
        self.events.append(("permission_cursor_close",))


class PermissionConnection:
    def __init__(self, events):
        self.events = events
        self.cursor_instance = PermissionCursor(events)

    def cursor(self):
        return self.cursor_instance

    def close(self):
        self.events.append(("permission_connection_close",))


class AccessCursor:
    def __init__(self, result):
        self.result = result
        self.query = None
        self.params = None

    def execute(self, query, params=None):
        self.query = query
        self.params = params

    def fetchone(self):
        return self.result


class RepositoryCursor:
    def __init__(self, events):
        self.events = events
        self.last_query = ""

    def execute(self, query, params=None):
        self.last_query = query
        self.events.append(("repository_query", query, params))

    def fetchone(self):
        query = self.last_query
        # Año lectivo, paso 3.7: la guardia de escritura ve 2026 activo.
        if "SELECT al.anio, al.estado" in query:
            return (2026, "activo")
        if "AS asignacion_academica_id" in query:
            return (23,)
        if "RETURNING id, version_revision, estado_revision" in query:
            return (31, 1, "pendiente")
        if "COUNT(*), COUNT(DISTINCT" in query:
            return (0, 0)
        if "WHERE pdc.id = %s" in query:
            return (
                31,
                23,
                1,
                "Unidad",
                "Proposito",
                "Clase",
                "Estandar",
                "DBA",
                "Competencias",
                "Actividad",
                "Tema",
                date(2026, 8, 22),
                None,
                None,
                9,
                "Ana Docente",
                "Quinto",
                "Matematicas",
                datetime(2026, 8, 22, tzinfo=timezone.utc),
                datetime(2026, 8, 22, tzinfo=timezone.utc),
                "pendiente",
                1,
                datetime(2026, 8, 22, tzinfo=timezone.utc),
                None,
                None,
                0,
                0,
                None,
            )
        if "SELECT COUNT(*)" in query:
            return (0,)
        raise AssertionError(f"fetchone inesperado para SQL: {query}")

    def fetchall(self):
        return []


def _install_database_doubles(monkeypatch):
    events = []

    def fake_get_connection():
        events.append(("permission_connection_open",))
        return PermissionConnection(events)

    @contextmanager
    def fake_get_cursor(commit=False):
        events.append(("repository_connection_open", commit))
        yield RepositoryCursor(events)
        events.append(("repository_connection_close", commit))

    monkeypatch.setattr(permissions, "get_connection", fake_get_connection)
    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)
    return events


def _event_count(events, name):
    return sum(event[0] == name for event in events)


def test_domain_boundary_is_five_own_product_files():
    discovered = {
        path.relative_to(ROOT).as_posix()
        for directory in (
            "app/routes",
            "app/controllers",
            "app/services",
            "app/repositories",
            "app/schemas",
        )
        for path in (ROOT / directory).glob("*plan_de_clases*.py")
    }

    assert discovered == DOMAIN_FILES
    # 1382 -> 1395: año lectivo, fase 3 (paso 3.5b), la lista de planes del
    # admin por año (repositorio y ruta). 1395 -> 1413: paso 3.7, la guardia
    # de escritura en crear, borrar imagen y marcar vista (quien guarda llega
    # hasta el repositorio, y la ruta del admin recibe al admin).
    assert sum(len(_source(path).splitlines()) for path in DOMAIN_FILES) == 1413
    own_source = "\n".join(_source(path) for path in DOMAIN_FILES)
    assert "planeador_anual" not in own_source
    assert "app.routes.observaciones" not in own_source


def test_router_has_exactly_eleven_entries_and_no_response_models():
    routes = [
        route
        for route in plan_de_clases.router.routes
        if isinstance(route, APIRoute)
    ]

    assert len(routes) == 11
    assert {
        (method, route.path)
        for route in routes
        for method in route.methods
    } == EXPECTED_ROUTES
    assert all(route.response_model is None for route in routes)


def test_declared_response_schema_is_unused_and_omits_two_observable_fields():
    assert {"created_at", "updated_at"}.isdisjoint(
        PlanDeClasesResponse.model_fields
    )
    assert {"created_at", "updated_at"}.issubset(
        plan_de_clases_repository._row_to_plan(tuple(range(28)))
    )


def test_create_schema_keeps_optional_concurrency_and_unbounded_period_and_text():
    model = PlanDeClasesCreate(
        asignacion_id=23,
        periodo=-9,
        unidad="x" * 4000,
        fecha=date(2026, 8, 22),
    )

    assert model.version_esperada is None
    assert model.periodo == -9
    assert len(model.unidad) == 4000


def test_sql_boundary_has_twenty_seven_repository_executions_and_no_shared_ones():
    repository_tree = _tree("app/repositories/plan_de_clases_repository.py")
    assert len(_execute_calls(repository_tree)) == 27
    for path in (
        "app/routes/plan_de_clases.py",
        "app/controllers/plan_de_clases_controller.py",
        "app/services/plan_de_clases_service.py",
    ):
        assert _execute_calls(_tree(path)) == []

    permission_source = _function_source(
        "app/core/permissions.py",
        "require_plan_de_clases_access",
    )
    upload_source = _function_source(
        "app/main.py",
        "_validar_acceso_archivo_upload",
    )
    assert "cursor.execute" not in permission_source
    assert "cursor.execute" not in upload_source
    assert "FROM plan_de_clases" not in permission_source
    assert "FROM plan_de_clases" not in upload_source
    assert "profesor_tiene_acceso_plan_de_clases_cursor" in permission_source
    assert "profesor_tiene_acceso_imagen_plan_de_clases_cursor" in upload_source


@pytest.mark.parametrize(
    ("function_name", "expected_sql", "arguments", "expected_params"),
    [
        (
            "profesor_tiene_acceso_plan_de_clases_cursor",
            PLAN_ACCESS_SQL,
            (15, 7),
            (15, 7),
        ),
        (
            "profesor_tiene_acceso_imagen_plan_de_clases_cursor",
            PLAN_IMAGE_ACCESS_SQL,
            ("uploads/tenant_demo/plan_de_clases/plan.png", 7),
            (
                "uploads/tenant_demo/plan_de_clases/plan.png",
                "uploads/tenant_demo/plan_de_clases/plan.png",
                7,
            ),
        ),
    ],
)
def test_access_repository_helpers_preserve_exact_sql_and_parameters(
    function_name,
    expected_sql,
    arguments,
    expected_params,
):
    function = getattr(plan_de_clases_repository, function_name)
    cursor = AccessCursor((1,))

    assert function(cursor, *arguments) is True
    assert cursor.query == expected_sql
    assert cursor.params == expected_params

    cursor.result = None
    assert function(cursor, *arguments) is False


def test_ownership_queries_do_not_filter_inactive_assignments():
    permission_source = _function_source(
        "app/repositories/plan_de_clases_repository.py",
        "profesor_tiene_acceso_plan_de_clases_cursor",
    )
    upload_source = _function_source(
        "app/repositories/plan_de_clases_repository.py",
        "profesor_tiene_acceso_imagen_plan_de_clases_cursor",
    )

    assert "profesor_id" in permission_source
    assert "profesor_id" in upload_source
    assert "activo" not in permission_source
    assert "activo" not in upload_source


def test_repository_resource_ownership_is_fixed_per_operation():
    tree = _tree("app/repositories/plan_de_clases_repository.py")
    observed = {}
    for function in (
        node for node in tree.body if isinstance(node, ast.FunctionDef)
    ):
        calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "get_cursor"
        ]
        if calls:
            assert len(calls) == 1
            commit = next(
                (
                    keyword.value.value
                    for keyword in calls[0].keywords
                    if keyword.arg == "commit"
                    and isinstance(keyword.value, ast.Constant)
                ),
                False,
            )
            observed[function.name] = commit

    assert observed == {
        "guardar_plan_de_clases": True,
        "obtener_plan_por_dia": False,
        "obtener_planes_por_asignacion": False,
        "obtener_plan_por_id": False,
        "listar_planes_admin": False,
        "actualizar_estado_revision_plan": True,
        "agregar_observacion_plan": True,
        "listar_observaciones_plan": False,
        "marcar_observacion_vista": True,
        "listar_notificaciones_admin": False,
        "listar_notificaciones_profesor": False,
        "eliminar_imagen_plan": True,
    }


def test_repository_emits_no_query_from_a_python_loop():
    tree = _tree("app/repositories/plan_de_clases_repository.py")
    loops = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While))
    ]

    assert all(_execute_calls(loop) == [] for loop in loops)
    assert plan_de_clases_repository.PLAN_SELECT.count(
        "FROM plan_de_clases_observaciones"
    ) == 3


def test_current_ddl_has_three_tables_and_their_integrity_guards():
    ddl = _source("migrations/base/20260813_esquema_base_tenant.sql")

    for table in (
        "plan_de_clases",
        "plan_de_clases_notificaciones_admin",
        "plan_de_clases_observaciones",
    ):
        assert ddl.count(f"CREATE TABLE IF NOT EXISTS {table} (") == 1
    assert "uq_plan_de_clases_asignacion_fecha" in ddl
    assert "ck_plan_de_clases_estado_revision" in ddl
    assert "ck_plan_de_clases_version_revision" in ddl
    assert "ck_plan_observacion_texto" in ddl
    assert "FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id)" in ddl
    assert "FOREIGN KEY (plan_id) REFERENCES plan_de_clases(id) ON DELETE CASCADE" in ddl


def test_http_notifications_preserve_403_and_query_validation():
    denied = _app_with_user({"id": 5, "rol": "estudiante", "tenant": "tenant_demo"})
    status_code, payload = _asgi_request(
        denied,
        "GET",
        "/notificaciones/planeadores",
    )
    assert (status_code, payload) == (403, {"detail": "No autorizado"})

    allowed = _app_with_user({"id": 5, "rol": "admin", "tenant": "tenant_demo"})
    status_code, payload = _asgi_request(
        allowed,
        "GET",
        "/notificaciones/planeadores?limit=0",
    )
    assert status_code == 422
    assert payload["detail"][0]["loc"] == ["query", "limit"]


def test_http_read_serializes_dates_without_response_model(monkeypatch):
    expected = {
        "id": 31,
        "fecha": date(2026, 8, 22),
        "created_at": datetime(2026, 8, 22, 15, 0, tzinfo=timezone.utc),
        "updated_at": None,
    }
    monkeypatch.setattr(
        plan_de_clases,
        "obtener_plan_del_dia_controller",
        lambda _assignment_id, _date: expected,
    )
    app = _app_with_user({"id": 1, "rol": "admin", "tenant": "tenant_demo"})

    status_code, payload = _asgi_request(
        app,
        "GET",
        "/plan-de-clases/23?fecha=2026-08-22",
    )

    assert status_code == 200
    assert payload == {
        "id": 31,
        "fecha": "2026-08-22",
        "created_at": "2026-08-22T15:00:00+00:00",
        "updated_at": None,
    }


def test_http_create_keeps_invalid_date_as_400(monkeypatch):
    monkeypatch.setattr(
        plan_de_clases,
        "crear_plan_de_clases_controller",
        lambda *_args: pytest.fail("No debe entrar al controlador"),
    )
    boundary = "plan-boundary"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="asignacion_id"\r\n\r\n'
        "23\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="fecha"\r\n\r\n'
        "fecha-invalida\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    app = _app_with_user({"id": 1, "rol": "admin", "tenant": "tenant_demo"})

    status_code, payload = _asgi_request(
        app,
        "POST",
        "/plan-de-clases",
        body=body,
        headers={"content-type": f"multipart/form-data; boundary={boundary}"},
    )

    assert status_code == 400
    assert "Invalid isoformat string" in payload["detail"]


def test_http_revision_schema_keeps_invalid_comment_as_422(monkeypatch):
    monkeypatch.setattr(
        plan_de_clases,
        "actualizar_revision_plan_controller",
        lambda *_args: pytest.fail("No debe entrar al controlador"),
    )
    app = _app_with_user({"id": 1, "rol": "admin", "tenant": "tenant_demo"})
    body = json.dumps(
        {"estado": "visto", "version": 2, "comentario": "No corresponde"}
    ).encode()

    status_code, payload = _asgi_request(
        app,
        "PATCH",
        "/admin/plan-de-clases/31/revision",
        body=body,
        headers={"content-type": "application/json"},
    )

    assert status_code == 422
    assert "El comentario solo se admite" in payload["detail"][0]["msg"]


@pytest.mark.parametrize(
    ("role", "expected_connections", "expected_queries"),
    [("admin", 1, 2), ("profesor", 2, 3)],
)
def test_assignment_history_has_constant_query_and_connection_counts(
    monkeypatch,
    role,
    expected_connections,
    expected_queries,
):
    events = _install_database_doubles(monkeypatch)

    result = plan_de_clases.obtener_planes_por_asignacion(
        asignacion_id=23,
        fecha=None,
        limit=None,
        offset=0,
        current_user={"id": 9, "rol": role, "tenant": "tenant_demo"},
    )

    assert result == []
    assert (
        _event_count(events, "permission_connection_open")
        + _event_count(events, "repository_connection_open")
    ) == expected_connections
    assert (
        _event_count(events, "permission_query")
        + _event_count(events, "repository_query")
    ) == expected_queries


# Año lectivo, paso 3.7: la guardia suma una consulta y ninguna conexion
# (antes 3 y 4).
@pytest.mark.parametrize(
    ("role", "expected_connections", "expected_queries"),
    [("admin", 1, 4), ("profesor", 2, 5)],
)
def test_create_without_version_or_images_has_constant_baseline(
    monkeypatch,
    role,
    expected_connections,
    expected_queries,
):
    events = _install_database_doubles(monkeypatch)

    result = plan_de_clases.crear_plan_de_clases(
        asignacion_id=23,
        version_esperada=None,
        periodo=1,
        unidad="",
        proposito="",
        clase="",
        estandar="",
        dba="",
        competencias="",
        actividad_casa="",
        tema="",
        fecha="2026-08-22",
        imagen1=None,
        imagen2=None,
        current_user={"id": 9, "rol": role, "tenant": "tenant_demo"},
    )

    assert result == {
        "mensaje": "Plan de clases guardado y enviado a administración",
        "id": 31,
        "version_revision": 1,
        "estado_revision": "pendiente",
    }
    assert (
        _event_count(events, "permission_connection_open")
        + _event_count(events, "repository_connection_open")
    ) == expected_connections
    assert (
        _event_count(events, "permission_query")
        + _event_count(events, "repository_query")
    ) == expected_queries


@pytest.mark.parametrize(
    ("role", "expected_connections", "expected_queries"),
    [("admin", 2, 2), ("profesor", 3, 3)],
)
def test_observation_list_opens_two_repository_connections(
    monkeypatch,
    role,
    expected_connections,
    expected_queries,
):
    events = _install_database_doubles(monkeypatch)

    result = plan_de_clases.listar_observaciones_plan(
        plan_id=31,
        current_user={"id": 9, "rol": role, "tenant": "tenant_demo"},
    )

    assert result == []
    assert _event_count(events, "repository_connection_open") == 2
    assert (
        _event_count(events, "permission_connection_open")
        + _event_count(events, "repository_connection_open")
    ) == expected_connections
    assert (
        _event_count(events, "permission_query")
        + _event_count(events, "repository_query")
    ) == expected_queries


@pytest.mark.parametrize("role", ["admin", "profesor"])
def test_notifications_use_one_connection_and_two_queries(monkeypatch, role):
    events = _install_database_doubles(monkeypatch)

    result = plan_de_clases.obtener_notificaciones_planeadores(
        limit=8,
        current_user={"id": 9, "rol": role, "tenant": "tenant_demo"},
    )

    assert result["total_no_leidas"] == 0
    assert result["items"] == []
    assert _event_count(events, "permission_connection_open") == 0
    assert _event_count(events, "repository_connection_open") == 1
    assert _event_count(events, "repository_query") == 2


def test_unbounded_history_and_observation_lists_are_current_contract():
    routes = {
        (next(iter(route.methods)), route.path): route
        for route in plan_de_clases.router.routes
        if isinstance(route, APIRoute)
    }
    history = routes[("GET", "/plan-de-clases/{asignacion_id}")]
    observations = routes[("GET", "/plan-de-clases/{plan_id}/observaciones")]
    history_limit = next(
        parameter
        for parameter in history.dependant.query_params
        if parameter.name == "limit"
    )

    assert history_limit.default is None
    assert observations.dependant.query_params == []
