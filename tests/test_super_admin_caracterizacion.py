"""Caracterización de la frontera privilegiada de ``super_admin``.

Fija rutas, permisos, autenticación pública, SQL, recursos, provisión de tenant,
DDL y consumidores antes y después de las extracciones del dominio.
"""

import ast
import inspect
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import psycopg2
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute

from app import main
from app.controllers import auth_controller, super_admin_controller
from app.core import super_admin
from app.globals import tenant_schema_var
from app.routes import super_admin as super_admin_routes


ROOT = Path(__file__).resolve().parents[1]
OWN_PRODUCT_FILES = {
    "app/routes/super_admin.py": 64,
    "app/controllers/super_admin_controller.py": 339,
    "app/core/super_admin.py": 100,
    "app/repositories/super_admin_repository.py": 121,
}
PUBLIC_TABLE_PATTERN = re.compile(
    r"\b(?:FROM|JOIN|INTO|UPDATE)\s+(?:public\.)?"
    r"(?:super_admins|colegios|tenant_suscripciones|"
    r"tenant_estado_auditoria|tenant_eventos_auditoria)\b",
    re.IGNORECASE,
)
TENANT_ROW = (
    1,
    "Colegio Demo",
    "demo",
    "tenant_demo",
    "activo",
    date(2026, 6, 1),
    date(2026, 7, 1),
    5,
)
TENANT_CREATE_PAYLOAD = {
    "nombre": "Colegio Nuevo",
    "codigo": "nuevo",
    "admin_nombre": "Admin Nuevo",
    "admin_email": "ADMIN@COLEGIO.COM",
    "admin_password": "Temporal123",
    "fecha_inicio": "2026-06-01",
    "fecha_proximo_pago": "2026-07-01",
    "dias_gracia": 5,
    "notas": "Plan mensual",
}


class CursorProbe:
    def __init__(self, *, fetchones=(), fetchalls=(), error_at=None, error=None):
        self.fetchones = list(fetchones)
        self.fetchalls = list(fetchalls)
        self.error_at = error_at
        self.error = error or RuntimeError("fallo simulado")
        self.calls = []
        self.closed = 0

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if self.error_at == len(self.calls):
            raise self.error

    def fetchone(self):
        return self.fetchones.pop(0) if self.fetchones else None

    def fetchall(self):
        return self.fetchalls.pop(0) if self.fetchalls else []

    def close(self):
        self.closed += 1


class ProvisioningCursor:
    def __init__(self, *, error_at=None, error=None, history_exists=True):
        self.error_at = error_at
        self.error = error or RuntimeError("fallo simulado")
        self.history_exists = history_exists
        self.calls = []
        self.pending = None
        self.closed = 0

    def execute(self, query, params=None):
        text = str(query)
        self.calls.append((text, params))
        if self.error_at == len(self.calls):
            raise self.error
        if "INSERT INTO public.colegios" in text:
            self.pending = (9, "Colegio Nuevo", "nuevo", "tenant_nuevo", "activo")
        elif "to_regclass" in text:
            self.pending = (
                ("public.schema_migrations",) if self.history_exists else (None,)
            )
        else:
            self.pending = None

    def fetchone(self):
        row, self.pending = self.pending, None
        return row

    def fetchall(self):
        return []

    def close(self):
        self.closed += 1


class ConnectionProbe:
    def __init__(self, cursor):
        self._cursor = cursor
        self.cursor_calls = 0
        self.commits = 0
        self.rollbacks = 0
        self.closed = 0

    def cursor(self):
        self.cursor_calls += 1
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed += 1


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _source(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _execute_count(relative_path):
    tree = ast.parse(_source(relative_path))
    return sum(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "execute"
        for node in ast.walk(tree)
    )


def _normalize_sql(query):
    return " ".join(str(query).split())


def _install_connection(monkeypatch, module, cursor):
    connection = ConnectionProbe(cursor)
    contexts = []

    def get_connection():
        contexts.append(tenant_schema_var.get())
        return connection

    monkeypatch.setattr(module, "get_connection", get_connection)
    return connection, contexts


def _super_admin_routes():
    return {
        (next(iter(route.methods)), route.path): route
        for route in super_admin_routes.router.routes
        if isinstance(route, APIRoute)
    }


def _probe_app(user=None, error=None):
    probe = FastAPI()
    probe.include_router(super_admin_routes.router)

    async def override_super_admin():
        if error:
            raise error
        return user or {"id": 7, "rol": "super_admin", "tenant": "public"}

    probe.dependency_overrides[super_admin.get_current_super_admin] = (
        override_super_admin
    )
    return probe


async def _asgi_request(app, method, target, *, json_body=None):
    parsed = urlsplit(target)
    body = b"" if json_body is None else json.dumps(json_body).encode()
    headers = []
    if json_body is not None:
        headers.append((b"content-type", b"application/json"))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": parsed.path,
        "raw_path": parsed.path.encode(),
        "query_string": parsed.query.encode(),
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
        "root_path": "",
    }
    messages = []
    request_sent = False

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body) if response_body else None


def test_frontera_archivos_y_sql_extraido_queda_fijada():
    assert {
        path: len(_source(path).splitlines()) for path in OWN_PRODUCT_FILES
    } == OWN_PRODUCT_FILES
    assert _execute_count("app/routes/super_admin.py") == 0
    assert _execute_count("app/controllers/super_admin_controller.py") == 13
    assert _execute_count("app/core/super_admin.py") == 0
    assert _execute_count("app/repositories/super_admin_repository.py") == 7
    assert (ROOT / "app/repositories/super_admin_repository.py").exists()
    assert not (ROOT / "app/repositories/super_admins_repository.py").exists()


def test_repositorio_fija_superficie_y_no_administra_recursos():
    repository_path = "app/repositories/super_admin_repository.py"
    tree = ast.parse(_source(repository_path))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert set(functions) == {
        "obtener_super_admin_por_email",
        "obtener_estado_super_admin",
        "listar_tenants",
        "listar_auditoria_tenant",
        "obtener_tenant_para_estado",
        "actualizar_estado_tenant",
        "registrar_auditoria_estado",
    }
    assert all(node.args.args[0].arg == "cursor" for node in functions.values())
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom)) for node in tree.body
    )

    source = _source(repository_path)
    for forbidden in (
        "get_connection",
        "get_cursor",
        "commit()",
        "rollback()",
        "close()",
    ):
        assert forbidden not in source


def test_cuatro_rutas_privilegiadas_y_login_compartido_quedan_montados():
    routes = _super_admin_routes()

    assert set(routes) == {
        ("GET", "/super-admin/tenants"),
        ("POST", "/super-admin/tenants"),
        ("PATCH", "/super-admin/tenants/{tenant_id}/estado"),
        ("GET", "/super-admin/tenants/{tenant_id}/estado-auditoria"),
    }
    assert all(route.response_model is None for route in routes.values())
    assert all(not inspect.iscoroutinefunction(route.endpoint) for route in routes.values())
    assert all(
        [dependency.call for dependency in route.dependant.dependencies]
        == [super_admin.get_current_super_admin]
        for route in routes.values()
    )

    mounted = {
        (method, route.path)
        for route in main.app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
        if route.path.startswith("/super-admin") or route.path == "/login"
    }
    assert mounted == set(routes) | {("POST", "/login")}


def test_schemas_inline_conservan_campos_requeridos_y_defaults():
    create_fields = super_admin_routes.TenantCreate.model_fields
    state_fields = super_admin_routes.TenantEstadoUpdate.model_fields

    assert set(create_fields) == {
        "nombre",
        "codigo",
        "admin_nombre",
        "admin_email",
        "admin_password",
        "fecha_inicio",
        "fecha_proximo_pago",
        "dias_gracia",
        "notas",
    }
    assert all(
        create_fields[name].is_required()
        for name in (
            "nombre",
            "codigo",
            "admin_nombre",
            "admin_email",
            "admin_password",
            "fecha_inicio",
            "fecha_proximo_pago",
        )
    )
    assert create_fields["dias_gracia"].default == 0
    assert create_fields["notas"].default is None
    assert set(state_fields) == {"estado", "motivo"}
    assert state_fields["estado"].is_required()
    assert state_fields["motivo"].default is None


@pytest.mark.anyio
async def test_http_rutas_conservan_status_200_payloads_y_super_admin_id(monkeypatch):
    calls = []
    tenants = [{"id": 1, "estado": "activo"}]
    created = {"id": 9, "estado": "activo"}
    updated = {"id": 9, "estado": "suspendido"}
    audit = [{"id": 3, "estado_nuevo": "suspendido"}]

    monkeypatch.setattr(
        super_admin_routes,
        "listar_tenants_controller",
        lambda: calls.append(("list",)) or tenants,
    )
    monkeypatch.setattr(
        super_admin_routes,
        "crear_tenant_controller",
        lambda data, super_admin_id: calls.append(("create", data, super_admin_id))
        or created,
    )
    monkeypatch.setattr(
        super_admin_routes,
        "actualizar_estado_tenant_controller",
        lambda tenant_id, estado, super_admin_id, motivo: calls.append(
            ("update", tenant_id, estado, super_admin_id, motivo)
        )
        or updated,
    )
    monkeypatch.setattr(
        super_admin_routes,
        "listar_auditoria_tenant_controller",
        lambda tenant_id: calls.append(("audit", tenant_id)) or audit,
    )
    app = _probe_app()

    responses = [
        await _asgi_request(app, "GET", "/super-admin/tenants"),
        await _asgi_request(
            app,
            "POST",
            "/super-admin/tenants",
            json_body=TENANT_CREATE_PAYLOAD,
        ),
        await _asgi_request(
            app,
            "PATCH",
            "/super-admin/tenants/9/estado",
            json_body={"estado": " suspendido ", "motivo": " Mora "},
        ),
        await _asgi_request(
            app,
            "GET",
            "/super-admin/tenants/9/estado-auditoria",
        ),
    ]

    assert responses == [
        (200, tenants),
        (200, created),
        (200, updated),
        (200, audit),
    ]
    assert calls[0] == ("list",)
    assert calls[1] == ("create", TENANT_CREATE_PAYLOAD, 7)
    assert calls[2] == ("update", 9, " suspendido ", 7, " Mora ")
    assert calls[3] == ("audit", 9)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("method", "target", "json_body"),
    [
        ("GET", "/super-admin/tenants", None),
        ("POST", "/super-admin/tenants", TENANT_CREATE_PAYLOAD),
        (
            "PATCH",
            "/super-admin/tenants/1/estado",
            {"estado": "suspendido"},
        ),
        ("GET", "/super-admin/tenants/1/estado-auditoria", None),
    ],
)
async def test_http_todas_las_rutas_conservan_401_del_guard(
    method,
    target,
    json_body,
):
    app = _probe_app(
        error=HTTPException(
            status_code=401,
            detail="No se pudo validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )
    )

    status_code, body = await _asgi_request(
        app,
        method,
        target,
        json_body=json_body,
    )

    assert status_code == 401
    assert body == {"detail": "No se pudo validar las credenciales"}


@pytest.mark.anyio
async def test_http_validacion_pydantic_ocurre_antes_del_controlador(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("el controlador no debe ejecutarse")

    monkeypatch.setattr(super_admin_routes, "crear_tenant_controller", fail)
    monkeypatch.setattr(super_admin_routes, "actualizar_estado_tenant_controller", fail)
    app = _probe_app()

    create_status, create_body = await _asgi_request(
        app,
        "POST",
        "/super-admin/tenants",
        json_body={"nombre": "Incompleto"},
    )
    state_status, state_body = await _asgi_request(
        app,
        "PATCH",
        "/super-admin/tenants/1/estado",
        json_body={},
    )

    assert create_status == 422
    assert {error["loc"][-1] for error in create_body["detail"]} == {
        "codigo",
        "admin_nombre",
        "admin_email",
        "admin_password",
        "fecha_inicio",
        "fecha_proximo_pago",
    }
    assert state_status == 422
    assert state_body["detail"][0]["loc"] == ["body", "estado"]


def test_codigos_de_login_privilegiado_y_dispatch_compartido_quedan_fijados(
    monkeypatch,
):
    assert super_admin.SUPER_ADMIN_LOGIN_CODES == {
        "super_admin",
        "superadmin",
        "plataforma",
    }

    calls = []
    monkeypatch.setattr(
        auth_controller,
        "authenticate_super_admin",
        lambda email, password, verify: calls.append((email, password, verify))
        or {"id": 7, "rol": "super_admin", "tenant": "public"},
    )
    monkeypatch.setattr(
        auth_controller,
        "get_tenant_by_code",
        lambda _code: (_ for _ in ()).throw(
            AssertionError("no debe resolver un tenant ordinario")
        ),
    )

    for code in (" SUPER_ADMIN ", "SuperAdmin", "PLATAFORMA"):
        result = auth_controller.login_controller("owner@app.com", "secret", code)
        assert result == {"id": 7, "rol": "super_admin", "tenant": "public"}

    assert len(calls) == 3
    assert all(call[:2] == ("owner@app.com", "secret") for call in calls)


@pytest.mark.parametrize(
    ("row", "password_valid", "expected", "verify_calls"),
    [
        (
            (7, "Owner", "owner@app.com", "hash", "activo"),
            True,
            {"id": 7, "nombre": "Owner", "rol": "super_admin", "tenant": "public"},
            [("secret", "hash")],
        ),
        (None, True, None, []),
        ((7, "Owner", "owner@app.com", "hash", "inactivo"), True, None, []),
        (
            (7, "Owner", "owner@app.com", "hash", "activo"),
            False,
            None,
            [("secret", "hash")],
        ),
    ],
)
def test_autenticacion_publica_normaliza_limpia_y_conserva_resultados(
    monkeypatch,
    row,
    password_valid,
    expected,
    verify_calls,
):
    cursor = CursorProbe(fetchones=[row])
    connection, contexts = _install_connection(monkeypatch, super_admin, cursor)
    calls = []

    def verify(password, hashed):
        calls.append((password, hashed))
        return password_valid

    outer = tenant_schema_var.set("tenant_outer")
    try:
        result = super_admin.authenticate_super_admin(
            " OWNER@APP.COM ",
            "secret",
            verify,
        )
        context_after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer)

    assert result == expected
    assert contexts == ["public"]
    assert context_after == "tenant_outer"
    assert len(cursor.calls) == 1
    assert _normalize_sql(cursor.calls[0][0]) == (
        "SELECT id, nombre, email, password, estado FROM public.super_admins "
        "WHERE email = %s"
    )
    assert cursor.calls[0][1] == ("owner@app.com",)
    assert calls == verify_calls
    assert (connection.commits, connection.rollbacks) == (0, 0)
    assert (cursor.closed, connection.closed) == (1, 1)


@pytest.mark.parametrize(
    ("row", "raises"),
    [(('activo',), False), (("INACTIVO",), True), (None, True)],
)
def test_revalidacion_publica_conserva_sql_contexto_y_error(monkeypatch, row, raises):
    cursor = CursorProbe(fetchones=[row])
    connection, contexts = _install_connection(monkeypatch, super_admin, cursor)

    outer = tenant_schema_var.set("tenant_outer")
    try:
        if raises:
            with pytest.raises(ValueError, match="Super admin no valido"):
                super_admin.validate_super_admin(7)
        else:
            super_admin.validate_super_admin(7)
        context_after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer)

    assert contexts == ["public"]
    assert context_after == "tenant_outer"
    assert _normalize_sql(cursor.calls[0][0]) == (
        "SELECT estado FROM public.super_admins WHERE id = %s"
    )
    assert cursor.calls[0][1] == (7,)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_listado_y_auditoria_usan_una_conexion_publica_y_una_consulta(monkeypatch):
    created_at = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    list_cursor = CursorProbe(fetchalls=[[TENANT_ROW]])
    list_connection, list_contexts = _install_connection(
        monkeypatch,
        super_admin_controller,
        list_cursor,
    )

    outer = tenant_schema_var.set("tenant_outer")
    try:
        tenants = super_admin_controller.listar_tenants_controller()
        list_context_after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer)

    audit_cursor = CursorProbe(
        fetchalls=[
            [
                (
                    10,
                    "activo",
                    "suspendido",
                    "Mora",
                    created_at,
                    "Owner",
                    "owner@app.com",
                )
            ]
        ]
    )
    audit_connection, audit_contexts = _install_connection(
        monkeypatch,
        super_admin_controller,
        audit_cursor,
    )

    outer = tenant_schema_var.set("tenant_outer")
    try:
        audit = super_admin_controller.listar_auditoria_tenant_controller(1)
        audit_context_after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer)

    assert tenants[0]["id"] == 1
    assert tenants[0]["estado_manual"] == "activo"
    assert audit == [
        {
            "id": 10,
            "estado_anterior": "activo",
            "estado_nuevo": "suspendido",
            "motivo": "Mora",
            "creado_en": "2026-06-01T12:00:00+00:00",
            "super_admin_nombre": "Owner",
            "super_admin_email": "owner@app.com",
        }
    ]
    assert list_contexts == ["public"]
    assert audit_contexts == ["public"]
    assert list_context_after == audit_context_after == "tenant_outer"
    assert len(list_cursor.calls) == len(audit_cursor.calls) == 1
    assert audit_cursor.calls[0][1] == (1,)
    assert (list_connection.commits, list_connection.rollbacks) == (0, 0)
    assert (audit_connection.commits, audit_connection.rollbacks) == (0, 0)
    assert (list_cursor.closed, list_connection.closed) == (1, 1)
    assert (audit_cursor.closed, audit_connection.closed) == (1, 1)


@pytest.mark.parametrize(
    ("rows", "expected_status", "queries", "commits", "rollbacks"),
    [([TENANT_ROW], "activo", 1, 0, 1), ([], None, 1, 0, 1)],
)
def test_estado_sin_cambio_o_ausente_revierte_sin_auditar(
    monkeypatch,
    rows,
    expected_status,
    queries,
    commits,
    rollbacks,
):
    cursor = CursorProbe(fetchones=rows)
    connection, contexts = _install_connection(
        monkeypatch,
        super_admin_controller,
        cursor,
    )

    outer = tenant_schema_var.set("tenant_outer")
    try:
        if expected_status is None:
            with pytest.raises(HTTPException) as exc:
                super_admin_controller.actualizar_estado_tenant_controller(
                    1,
                    "activo",
                    7,
                )
            assert exc.value.status_code == 404
        else:
            result = super_admin_controller.actualizar_estado_tenant_controller(
                1,
                " ACTIVO ",
                7,
                " Sin cambio ",
            )
            assert result["estado_manual"] == expected_status
        context_after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer)

    assert contexts == ["public"]
    assert context_after == "tenant_outer"
    assert len(cursor.calls) == queries
    assert cursor.calls[0][1] == (1,)
    assert (connection.commits, connection.rollbacks) == (commits, rollbacks)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_estado_modificado_conserva_tres_consultas_orden_y_auditoria(monkeypatch):
    updated_row = (1, "Colegio Demo", "demo", "tenant_demo", "suspendido")
    cursor = CursorProbe(fetchones=[TENANT_ROW, updated_row])
    connection, contexts = _install_connection(
        monkeypatch,
        super_admin_controller,
        cursor,
    )

    result = super_admin_controller.actualizar_estado_tenant_controller(
        1,
        " SUSPENDIDO ",
        7,
        " Mora prolongada ",
    )

    assert result["estado"] == "suspendido"
    assert result["estado_manual"] == "suspendido"
    assert contexts == ["public"]
    assert len(cursor.calls) == 3
    assert "FROM public.colegios" in str(cursor.calls[0][0])
    assert "UPDATE public.colegios" in str(cursor.calls[1][0])
    assert "INSERT INTO public.tenant_estado_auditoria" in str(cursor.calls[2][0])
    assert cursor.calls[0][1] == (1,)
    assert cursor.calls[1][1] == ("suspendido", 1)
    assert cursor.calls[2][1] == (
        1,
        "activo",
        "suspendido",
        "Mora prolongada",
        7,
    )
    assert (connection.commits, connection.rollbacks) == (1, 0)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_alta_http_con_historial_y_auditoria_usa_trece_operaciones_constantes(
    monkeypatch,
):
    cursor = ProvisioningCursor()
    connection, contexts = _install_connection(
        monkeypatch,
        super_admin_controller,
        cursor,
    )
    hashes = []
    monkeypatch.setattr(
        super_admin_controller,
        "get_password_hash",
        lambda password: hashes.append(password) or f"hash:{password}",
    )

    outer = tenant_schema_var.set("tenant_outer")
    try:
        result = super_admin_controller.crear_tenant_controller(
            dict(TENANT_CREATE_PAYLOAD),
            super_admin_id=7,
        )
        context_after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer)

    assert result == {
        "id": 9,
        "nombre": "Colegio Nuevo",
        "subdominio": "nuevo",
        "esquema_db": "tenant_nuevo",
        "estado": "activo",
        "estado_manual": "activo",
        "fecha_inicio": "2026-06-01",
        "fecha_proximo_pago": "2026-07-01",
        "dias_gracia": 5,
    }
    assert contexts == ["public"]
    assert context_after == "tenant_outer"
    assert len(cursor.calls) == 13
    assert "INSERT INTO public.colegios" in cursor.calls[0][0]
    assert "CREATE SCHEMA" in cursor.calls[1][0]
    assert "SET LOCAL search_path" in cursor.calls[2][0]
    assert cursor.calls[3][0] == super_admin_controller.ESQUEMA_BASE_TENANT.read_text(
        encoding="utf-8"
    )
    assert "to_regclass" in cursor.calls[4][0]
    assert "INSERT INTO public.schema_migrations" in cursor.calls[5][0]
    assert "SET search_path TO" in cursor.calls[6][0]
    assert "INSERT INTO institucion_branding" in cursor.calls[7][0]
    assert "INSERT INTO plantilla_impresion" in cursor.calls[8][0]
    assert "INSERT INTO usuarios" in cursor.calls[9][0]
    assert cursor.calls[10][0] == "SET search_path TO public"
    assert "INSERT INTO public.tenant_suscripciones" in cursor.calls[11][0]
    assert "INSERT INTO public.tenant_eventos_auditoria" in cursor.calls[12][0]
    assert cursor.calls[0][1] == ("Colegio Nuevo", "nuevo", "tenant_nuevo")
    assert cursor.calls[5][1] == (
        "tenant_nuevo",
        super_admin_controller.settings.DEFAULT_TENANT_SCHEMA,
    )
    assert cursor.calls[9][1] == (
        "Admin Nuevo",
        "admin@colegio.com",
        "hash:Temporal123",
    )
    assert cursor.calls[11][1] == (
        9,
        date(2026, 6, 1),
        date(2026, 7, 1),
        5,
        "Plan mensual",
    )
    assert cursor.calls[12][1] == (
        9,
        "tenant_creado",
        "Colegio creado con admin inicial admin@colegio.com",
        7,
    )
    assert hashes == ["Temporal123"]
    assert (connection.commits, connection.rollbacks) == (1, 0)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_alta_revierte_toda_la_transaccion_y_restaura_contexto_si_falla(monkeypatch):
    cursor = ProvisioningCursor(error_at=8)
    connection, contexts = _install_connection(
        monkeypatch,
        super_admin_controller,
        cursor,
    )
    monkeypatch.setattr(
        super_admin_controller,
        "get_password_hash",
        lambda password: f"hash:{password}",
    )

    outer = tenant_schema_var.set("tenant_outer")
    try:
        with pytest.raises(RuntimeError, match="fallo simulado"):
            super_admin_controller.crear_tenant_controller(
                dict(TENANT_CREATE_PAYLOAD),
                super_admin_id=7,
            )
        context_after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer)

    assert contexts == ["public"]
    assert context_after == "tenant_outer"
    assert len(cursor.calls) == 8
    assert (connection.commits, connection.rollbacks) == (0, 1)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_integrity_error_del_alta_conserva_409_y_limpieza(monkeypatch):
    cursor = ProvisioningCursor(error_at=1, error=psycopg2.IntegrityError("duplicado"))
    connection, _contexts = _install_connection(
        monkeypatch,
        super_admin_controller,
        cursor,
    )

    with pytest.raises(HTTPException) as exc:
        super_admin_controller.crear_tenant_controller(
            dict(TENANT_CREATE_PAYLOAD),
            super_admin_id=7,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "El codigo del colegio o el correo del admin ya existe"
    assert (connection.commits, connection.rollbacks) == (0, 1)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_no_hay_execute_dentro_de_bucles_en_la_frontera_propia():
    for relative_path in OWN_PRODUCT_FILES:
        tree = ast.parse(_source(relative_path))
        loop_executes = [
            call
            for loop in ast.walk(tree)
            if isinstance(loop, (ast.For, ast.AsyncFor, ast.While))
            for call in ast.walk(loop)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "execute"
        ]
        assert loop_executes == [], relative_path


def test_consumidores_directos_de_tablas_publicas_quedan_enumerados():
    consumers = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "app").rglob("*.py")
        if PUBLIC_TABLE_PATTERN.search(path.read_text(encoding="utf-8"))
    }

    assert consumers == {
        "app/controllers/super_admin_controller.py",
        "app/core/tenant_status.py",
        "app/repositories/super_admin_repository.py",
    }


def test_ddl_publico_fija_unicidad_referencias_y_hueco_de_colegios():
    super_admins = _source("migrations/public/20260530_super_admins.sql")
    subscriptions = _source(
        "migrations/public/20260601_tenant_suscripciones.sql"
    )
    events = _source("migrations/public/20260601_tenant_eventos_auditoria.sql")
    states = _source("migrations/public/20260601_tenant_estado_auditoria.sql")
    legacy = _source("scripts/legacy/setup_saas.py")
    public_migrations = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "migrations/public").glob("*.sql")
    )

    assert "email VARCHAR(255) NOT NULL UNIQUE" in super_admins
    assert "estado VARCHAR(30) NOT NULL DEFAULT 'activo'" in super_admins
    assert "CHECK" not in super_admins
    assert "tenant_id INTEGER NOT NULL UNIQUE" in subscriptions
    assert "ON DELETE CASCADE" in subscriptions
    assert "CHECK (dias_gracia >= 0)" in subscriptions
    assert "REFERENCES public.colegios(id)" in events
    assert "REFERENCES public.super_admins(id)" in events
    assert "ON DELETE" not in events
    assert "REFERENCES public.colegios(id)" in states
    assert "REFERENCES public.super_admins(id)" in states
    assert "ON DELETE" not in states
    assert "CREATE TABLE IF NOT EXISTS public.colegios" not in public_migrations
    assert "CREATE TABLE IF NOT EXISTS public.colegios" in legacy
    assert "subdominio VARCHAR(100) UNIQUE NOT NULL" in legacy
    assert "esquema_db VARCHAR(100) UNIQUE NOT NULL" in legacy
