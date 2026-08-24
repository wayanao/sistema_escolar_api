"""Caracterización de la frontera de profesores para la subcapa 7.0.

Complementa las pruebas heredadas de catálogo y de la función de clases sin
consumidores. Fija la frontera, los contratos HTTP, SQL y parámetros, recursos,
conteos por camino, DDL y consumidores externos antes de cualquier extracción.
"""

import ast
import inspect
import json
import re
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from psycopg2 import IntegrityError

from app import main
from app.controllers import profesor_controller
from app.dependencies import get_current_active_admin, get_current_user
from app.routes import profesores as profesores_routes
from app.schemas.profesor import ProfesorCreate, ProfesorEstadoUpdate


ROOT = Path(__file__).resolve().parents[1]
PROFESORES_PRODUCT_FILES = {
    "app/routes/profesores.py": 80,
    "app/controllers/profesor_controller.py": 314,
    "app/repositories/profesores_repository.py": 119,
    "app/schemas/profesor.py": 20,
}
PROFESORES_REPOSITORY = "app/repositories/profesores_repository.py"
PROFESORES_REPOSITORY_FUNCTIONS = {
    "obtener_profesor_por_documento",
    "obtener_profesor_por_email",
    "crear_profesor",
    "listar_profesores",
    "contar_profesores",
    "listar_profesores_paginados",
    "actualizar_profesor_con_password",
    "actualizar_profesor_sin_password",
    "actualizar_estado_profesor",
}
PROFESOR_ROW = (
    7,
    "ANA",
    "PÉREZ",
    "CC 123",
    "ana@example.com",
    "555",
    1250000,
    "activo",
)
TABLE_SQL_PATTERN = re.compile(
    r"\b(?:FROM|JOIN|INTO|UPDATE|DELETE\s+FROM)\s+profesor\b",
    re.IGNORECASE,
)


class CursorProbe:
    def __init__(self, *, fetchones=(), fetchalls=(), error_at=None, error=None):
        self.fetchones = list(fetchones)
        self.fetchalls = list(fetchalls)
        self.error_at = error_at
        self.error = error
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


def _public_functions(relative_path):
    tree = ast.parse(_source(relative_path))
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }


def _normalize_sql(query):
    return " ".join(query.split())


def _profesores_routes():
    return {
        (next(iter(route.methods)), route.path): route
        for route in profesores_routes.router.routes
        if isinstance(route, APIRoute)
    }


def _probe_app(user):
    probe = FastAPI()
    probe.include_router(profesores_routes.router)

    async def override_user():
        return user

    probe.dependency_overrides[get_current_user] = override_user
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


def _profesor_data(**overrides):
    values = {
        "nombre": "Ana",
        "apellido": "Pérez",
        "documento_identidad": "CC 123",
        "email": "ana@example.com",
        "telefono": "555",
        "password": "secreto",
        "sueldo": 1250000.0,
        "estado": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _profesor_json(**overrides):
    values = vars(_profesor_data()).copy()
    values.update(overrides)
    return values


def _install_connection(monkeypatch, cursor):
    connection = ConnectionProbe(cursor)
    calls = []

    def get_connection():
        calls.append(None)
        return connection

    monkeypatch.setattr(profesor_controller, "get_connection", get_connection)
    return connection, calls


def test_frontera_archivos_sql_repositorio_y_montaje_queda_fijada():
    assert {
        path: len(_source(path).splitlines())
        for path in PROFESORES_PRODUCT_FILES
    } == PROFESORES_PRODUCT_FILES
    assert _execute_count("app/routes/profesores.py") == 0
    assert (ROOT / PROFESORES_REPOSITORY).exists()
    assert _execute_count("app/controllers/profesor_controller.py") == 1
    assert _execute_count(PROFESORES_REPOSITORY) == 9
    assert _execute_count("app/schemas/profesor.py") == 0
    assert not (ROOT / "app/repositories/profesor_repository.py").exists()

    mounted = {
        (method.upper(), path)
        for path, operations in main.app.openapi()["paths"].items()
        if path.startswith("/profesores")
        for method in operations
        if method in {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
    }
    assert mounted == {
        ("POST", "/profesores"),
        ("GET", "/profesores"),
        ("PUT", "/profesores/{profesor_id}"),
        ("PATCH", "/profesores/{profesor_id}/estado"),
        ("GET", "/profesores/{profesor_id}/disponibilidad"),
        ("GET", "/profesores/{profesor_id}/cursos"),
    }


def test_repositorio_fija_superficie_y_no_administra_recursos():
    functions = _public_functions(PROFESORES_REPOSITORY)

    assert set(functions) == PROFESORES_REPOSITORY_FUNCTIONS
    assert all(function.args.args[0].arg == "cursor" for function in functions.values())

    source = _source(PROFESORES_REPOSITORY)
    for forbidden in (
        "get_connection",
        "get_cursor",
        "commit()",
        "rollback()",
        ".close()",
    ):
        assert forbidden not in source


def test_controlador_conserva_propiedad_de_recursos_y_transacciones():
    source = _source("app/controllers/profesor_controller.py")

    assert source.count("get_connection()") == 5
    assert source.count("get_cursor()") == 1
    assert source.count("conn.commit()") == 3
    assert source.count("conn.rollback()") == 6
    assert source.count("cursor.close()") == 5
    assert source.count("conn.close()") == 5


def test_consumidores_sql_directos_de_profesor_quedan_enumerados():
    consumers = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "app").rglob("*.py")
        if TABLE_SQL_PATTERN.search(path.read_text(encoding="utf-8"))
    }

    assert consumers == {
        "app/controllers/auth_controller.py",
        "app/controllers/nomina_controller.py",
        "app/controllers/prestamo_controller.py",
        "app/dependencies.py",
        "app/repositories/asignaciones_repository.py",
        "app/repositories/boletin_repository.py",
        "app/repositories/estudiantes_repository.py",
        "app/repositories/notas_repository.py",
        "app/repositories/plan_de_clases_repository.py",
        "app/repositories/profesores_repository.py",
        "app/repositories/reportes_repository.py",
    }


def test_no_hay_execute_dentro_de_bucles_en_la_frontera_propia():
    for relative_path in (
        "app/controllers/profesor_controller.py",
        PROFESORES_REPOSITORY,
    ):
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


def test_ddl_fija_unicidad_estado_y_tres_referencias_externas():
    base = _source("migrations/base/20260813_esquema_base_tenant.sql")
    migration = _source("migrations/20260604_profesor_estado.sql")

    assert "CREATE TABLE IF NOT EXISTS profesor (" in base
    assert "CONSTRAINT profesor_pkey PRIMARY KEY (id)" in base
    assert "CONSTRAINT profesor_email_key UNIQUE (email)" in base
    assert "CONSTRAINT profesor_documento_identidad_key UNIQUE (documento_identidad)" in base
    assert "CONSTRAINT unique_documento_identidad UNIQUE (documento_identidad)" in base
    assert "estado character varying(30)," in base
    assert base.count("REFERENCES profesor(id)") == 3
    assert (
        "asignaciones_profesor_id_fkey FOREIGN KEY (profesor_id) "
        "REFERENCES profesor(id);"
    ) in base
    assert (
        "nomina_profesor_id_fkey FOREIGN KEY (profesor_id) "
        "REFERENCES profesor(id) ON DELETE CASCADE;"
    ) in base
    assert (
        "prestamos_profesor_id_fkey FOREIGN KEY (profesor_id) "
        "REFERENCES profesor(id) ON DELETE CASCADE;"
    ) in base
    assert "ADD COLUMN IF NOT EXISTS estado VARCHAR(30)" in migration
    assert "SET estado = 'activo'" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_profesor_estado" in migration


def test_rutas_metodos_permiso_sync_y_response_model_quedan_fijados():
    routes = _profesores_routes()
    assert set(routes) == {
        ("POST", "/profesores"),
        ("GET", "/profesores"),
        ("PUT", "/profesores/{profesor_id}"),
        ("PATCH", "/profesores/{profesor_id}/estado"),
    }

    for route in routes.values():
        assert [dependency.dependency for dependency in route.dependencies] == [
            get_current_active_admin
        ]
        assert route.response_model is None
        assert not inspect.iscoroutinefunction(route.endpoint)


def test_esquemas_fijan_campos_obligatorios_email_estado_y_password_de_put():
    data = ProfesorCreate(**_profesor_json(estado="inactivo"))
    assert data.model_dump() == _profesor_json(estado="inactivo")
    assert ProfesorEstadoUpdate(estado="activo").estado == "activo"

    with pytest.raises(ValueError):
        ProfesorCreate(**_profesor_json(email="no-es-email"))
    with pytest.raises(ValueError):
        ProfesorCreate(**{key: value for key, value in _profesor_json().items() if key != "password"})
    with pytest.raises(ValueError):
        ProfesorEstadoUpdate(estado="retirado")


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("role", "expected_status"),
    [("admin", 200), ("profesor", 403)],
)
async def test_post_http_exige_admin_y_conserva_status_y_payload(
    monkeypatch,
    role,
    expected_status,
):
    calls = []
    monkeypatch.setattr(
        profesores_routes,
        "crear_profesor_controller",
        lambda data: calls.append(data) or 17,
    )
    app = _probe_app({"id": 1, "rol": role, "tenant": "tenant_demo"})

    status_code, body = await _asgi_request(
        app,
        "POST",
        "/profesores",
        json_body=_profesor_json(),
    )

    assert status_code == expected_status
    if role == "admin":
        assert body == {"mensaje": "Profesor creado correctamente", "id": 17}
        assert len(calls) == 1
    else:
        assert body == {"detail": "No tienes los permisos necesarios"}
        assert calls == []


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "expected_status", "detail"),
    [
        (profesor_controller.ProfesorDuplicadoError("duplicado"), 409, "duplicado"),
        (ValueError("invalido"), 422, "invalido"),
    ],
)
async def test_post_http_traduce_errores_de_dominio(
    monkeypatch,
    error,
    expected_status,
    detail,
):
    def fail(_data):
        raise error

    monkeypatch.setattr(profesores_routes, "crear_profesor_controller", fail)
    app = _probe_app({"id": 1, "rol": "admin", "tenant": "tenant_demo"})

    status_code, body = await _asgi_request(
        app,
        "POST",
        "/profesores",
        json_body=_profesor_json(),
    )

    assert status_code == expected_status
    assert body == {"detail": detail}


@pytest.mark.anyio
async def test_get_http_conserva_lista_legacy_y_paginacion(monkeypatch):
    calls = []
    monkeypatch.setattr(
        profesores_routes,
        "obtener_profesores_controller",
        lambda estado="activo": calls.append(("legacy", estado)) or [{"id": 1}],
    )
    monkeypatch.setattr(
        profesores_routes,
        "obtener_profesores_paginado_controller",
        lambda **kwargs: calls.append(("paginado", kwargs))
        or {"total": 1, "limit": 10, "offset": 5, "items": [{"id": 2}]},
    )
    app = _probe_app({"id": 1, "rol": "admin", "tenant": "tenant_demo"})

    legacy_status, legacy_body = await _asgi_request(
        app,
        "GET",
        "/profesores?busqueda=ignorada&offset=99&estado=todos",
    )
    paged_status, paged_body = await _asgi_request(
        app,
        "GET",
        "/profesores?limit=10&offset=5&busqueda=ana&estado=inactivo",
    )

    assert (legacy_status, legacy_body) == (200, [{"id": 1}])
    assert (paged_status, paged_body) == (
        200,
        {"total": 1, "limit": 10, "offset": 5, "items": [{"id": 2}]},
    )
    assert calls == [
        ("legacy", "todos"),
        (
            "paginado",
            {"limit": 10, "offset": 5, "busqueda": "ana", "estado": "inactivo"},
        ),
    ]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("target", "detail_location"),
    [
        ("/profesores?estado=retirado", None),
        ("/profesores?limit=0", ["query", "limit"]),
        ("/profesores?offset=-1", ["query", "offset"]),
    ],
)
async def test_get_http_rechaza_filtros_invalidos(target, detail_location):
    app = _probe_app({"id": 1, "rol": "admin", "tenant": "tenant_demo"})

    status_code, body = await _asgi_request(app, "GET", target)

    assert status_code == 422
    if detail_location is None:
        assert body == {"detail": "Filtro de estado de profesor invalido"}
    else:
        assert body["detail"][0]["loc"] == detail_location


@pytest.mark.anyio
async def test_put_http_mapea_no_encontrado_y_exige_password_en_el_body(monkeypatch):
    monkeypatch.setattr(
        profesores_routes,
        "actualizar_profesor_controller",
        lambda _id, _data: {"error": "Profesor no encontrado"},
    )
    app = _probe_app({"id": 1, "rol": "admin", "tenant": "tenant_demo"})

    missing_status, missing_body = await _asgi_request(
        app,
        "PUT",
        "/profesores/99",
        json_body=_profesor_json(),
    )
    invalid = _profesor_json()
    del invalid["password"]
    schema_status, schema_body = await _asgi_request(
        app,
        "PUT",
        "/profesores/99",
        json_body=invalid,
    )

    assert (missing_status, missing_body) == (
        404,
        {"detail": "Profesor no encontrado"},
    )
    assert schema_status == 422
    assert schema_body["detail"][0]["loc"] == ["body", "password"]


@pytest.mark.anyio
async def test_patch_http_conserva_payload_y_validacion_literal(monkeypatch):
    calls = []
    monkeypatch.setattr(
        profesores_routes,
        "actualizar_estado_profesor_controller",
        lambda profesor_id, estado: calls.append((profesor_id, estado))
        or {"mensaje": "Estado de profesor actualizado", "id": profesor_id, "estado": estado},
    )
    app = _probe_app({"id": 1, "rol": "admin", "tenant": "tenant_demo"})

    ok_status, ok_body = await _asgi_request(
        app,
        "PATCH",
        "/profesores/8/estado",
        json_body={"estado": "inactivo"},
    )
    invalid_status, invalid_body = await _asgi_request(
        app,
        "PATCH",
        "/profesores/8/estado",
        json_body={"estado": "retirado"},
    )

    assert (ok_status, ok_body) == (
        200,
        {"mensaje": "Estado de profesor actualizado", "id": 8, "estado": "inactivo"},
    )
    assert calls == [(8, "inactivo")]
    assert invalid_status == 422
    assert invalid_body["detail"][0]["loc"] == ["body", "estado"]


def test_crear_normaliza_valida_hashea_y_confirma_en_una_conexion(monkeypatch):
    cursor = CursorProbe(fetchones=[None, None, (41,)])
    connection, connections = _install_connection(monkeypatch, cursor)
    monkeypatch.setattr(
        profesor_controller,
        "get_password_hash",
        lambda password: f"HASH<{password}>",
    )

    result = profesor_controller.crear_profesor_controller(
        _profesor_data(
            nombre="  Ana   María ",
            apellido=" péRez ",
            documento_identidad="  CC  123 ",
            email=" ANA@Example.COM ",
            telefono=" 555 ",
            estado=" INACTIVO ",
        )
    )

    assert result == 41
    assert len(connections) == 1
    assert len(cursor.calls) == 3
    assert [_normalize_sql(query) for query, _params in cursor.calls] == [
        (
            "SELECT id FROM profesor WHERE TRIM(documento_identidad) = %s "
            "AND (%s IS NULL OR id <> %s) LIMIT 1"
        ),
        (
            "SELECT id FROM profesor WHERE LOWER(TRIM(email)) = %s "
            "AND (%s IS NULL OR id <> %s) LIMIT 1"
        ),
        (
            "INSERT INTO profesor ( nombre, apellido, documento_identidad, email, "
            "telefono, password, sueldo, estado ) VALUES "
            "(%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id"
        ),
    ]
    assert cursor.calls[0][1] == ("CC 123", None, None)
    assert cursor.calls[1][1] == ("ana@example.com", None, None)
    assert cursor.calls[2][1] == (
        "ANA MARÍA",
        "PÉREZ",
        "CC 123",
        "ana@example.com",
        " 555 ",
        "HASH<secreto>",
        1250000.0,
        "inactivo",
    )
    assert (connection.commits, connection.rollbacks) == (1, 0)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_crear_duplicado_prioriza_documento_y_revierte(monkeypatch):
    cursor = CursorProbe(fetchones=[(7,)])
    connection, _ = _install_connection(monkeypatch, cursor)

    with pytest.raises(
        profesor_controller.ProfesorDuplicadoError,
        match="documento 'CC 123'",
    ):
        profesor_controller.crear_profesor_controller(_profesor_data())

    assert len(cursor.calls) == 1
    assert (connection.commits, connection.rollbacks) == (0, 1)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_crear_traduce_integrity_error_y_revierte(monkeypatch):
    cursor = CursorProbe(
        fetchones=[None, None],
        error_at=3,
        error=IntegrityError("unique"),
    )
    connection, _ = _install_connection(monkeypatch, cursor)
    monkeypatch.setattr(profesor_controller, "get_password_hash", lambda _value: "hash")

    with pytest.raises(
        profesor_controller.ProfesorDuplicadoError,
        match="documento o email",
    ):
        profesor_controller.crear_profesor_controller(_profesor_data())

    assert len(cursor.calls) == 3
    assert (connection.commits, connection.rollbacks) == (0, 1)
    assert (cursor.closed, connection.closed) == (1, 1)


@pytest.mark.parametrize(
    ("estado", "expected_params", "where_present"),
    [("activo", ["activo"], True), ("todos", [], False)],
)
def test_listado_legacy_usa_una_conexion_y_conserva_forma(
    monkeypatch,
    estado,
    expected_params,
    where_present,
):
    cursor = CursorProbe(fetchalls=[[PROFESOR_ROW]])
    connection, connections = _install_connection(monkeypatch, cursor)

    result = profesor_controller.obtener_profesores_controller(estado=estado)

    assert result == [
        {
            "id": 7,
            "nombre": "ANA",
            "apellido": "PÉREZ",
            "documento": "CC 123",
            "email": "ana@example.com",
            "telefono": "555",
            "sueldo": 1250000,
            "estado": "activo",
        }
    ]
    assert len(connections) == 1
    assert len(cursor.calls) == 1
    where_sql = (
        " WHERE COALESCE(LOWER(estado), 'activo') = %s" if where_present else ""
    )
    assert _normalize_sql(cursor.calls[0][0]) == (
        "SELECT id, nombre, apellido, documento_identidad, email, telefono, sueldo, "
        "COALESCE(LOWER(estado), 'activo') AS estado FROM profesor"
        f"{where_sql} ORDER BY id"
    )
    assert cursor.calls[0][1] == expected_params
    assert ("WHERE" in cursor.calls[0][0]) is where_present
    assert (connection.commits, connection.rollbacks) == (0, 0)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_listado_paginado_cuenta_y_lista_con_parametros_exactos(monkeypatch):
    cursor = CursorProbe(fetchones=[(2,)], fetchalls=[[PROFESOR_ROW]])
    connection, connections = _install_connection(monkeypatch, cursor)

    result = profesor_controller.obtener_profesores_paginado_controller(
        limit=25,
        offset=50,
        busqueda="Ana",
        estado="inactivo",
    )

    filtros = ["inactivo", "%Ana%", "%Ana%", "%Ana%"]
    assert result == {
        "total": 2,
        "limit": 25,
        "offset": 50,
        "items": [
            {
                "id": 7,
                "nombre": "ANA",
                "apellido": "PÉREZ",
                "documento": "CC 123",
                "email": "ana@example.com",
                "telefono": "555",
                "sueldo": 1250000,
                "estado": "activo",
            }
        ],
    }
    assert len(connections) == 1
    assert len(cursor.calls) == 2
    expected_where = (
        "WHERE COALESCE(LOWER(estado), 'activo') = %s AND ( "
        "LOWER(nombre || ' ' || apellido) LIKE LOWER(%s) OR "
        "LOWER(COALESCE(email, '')) LIKE LOWER(%s) OR "
        "LOWER(COALESCE(documento_identidad, '')) LIKE LOWER(%s) )"
    )
    assert _normalize_sql(cursor.calls[0][0]) == (
        f"SELECT COUNT(*) FROM profesor {expected_where}"
    )
    assert _normalize_sql(cursor.calls[1][0]) == (
        "SELECT id, nombre, apellido, documento_identidad, email, telefono, sueldo, "
        "COALESCE(LOWER(estado), 'activo') AS estado FROM profesor "
        f"{expected_where} ORDER BY id LIMIT %s OFFSET %s"
    )
    assert cursor.calls[0][1] == filtros
    assert cursor.calls[1][1] == filtros + [25, 50]
    assert (connection.commits, connection.rollbacks) == (0, 0)
    assert (cursor.closed, connection.closed) == (1, 1)


@pytest.mark.parametrize(
    ("password", "query_has_password", "expected_password"),
    [("", False, None), ("nueva", True, "HASH<nueva>")],
)
def test_actualizar_conserva_las_dos_formas_sql_y_confirma(
    monkeypatch,
    password,
    query_has_password,
    expected_password,
):
    cursor = CursorProbe(fetchones=[None, None, (9,)])
    connection, connections = _install_connection(monkeypatch, cursor)
    hashes = []
    monkeypatch.setattr(
        profesor_controller,
        "get_password_hash",
        lambda value: hashes.append(value) or f"HASH<{value}>",
    )

    result = profesor_controller.actualizar_profesor_controller(
        9,
        _profesor_data(password=password, estado=None),
    )

    assert result == {"mensaje": "Profesor actualizado correctamente"}
    assert len(connections) == 1
    assert len(cursor.calls) == 3
    update_query, update_params = cursor.calls[2]
    expected_set = (
        "SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, "
        "telefono = %s, password = %s, sueldo = %s, "
        "estado = COALESCE(%s, estado, 'activo')"
        if query_has_password
        else (
            "SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, "
            "telefono = %s, sueldo = %s, estado = COALESCE(%s, estado, 'activo')"
        )
    )
    assert _normalize_sql(update_query) == (
        f"UPDATE profesor {expected_set} WHERE id = %s RETURNING id"
    )
    assert ("password = %s" in update_query) is query_has_password
    assert update_params[-2:] == (None, 9)
    assert hashes == ([password] if query_has_password else [])
    if query_has_password:
        assert expected_password in update_params
    assert (connection.commits, connection.rollbacks) == (1, 0)
    assert (cursor.closed, connection.closed) == (1, 1)


def test_actualizar_inexistente_valida_unicidad_antes_y_revierte(monkeypatch):
    cursor = CursorProbe(fetchones=[None, None, None])
    connection, _ = _install_connection(monkeypatch, cursor)

    result = profesor_controller.actualizar_profesor_controller(
        99,
        _profesor_data(password=""),
    )

    assert result == {"error": "Profesor no encontrado"}
    assert len(cursor.calls) == 3
    assert cursor.calls[0][1] == ("CC 123", 99, 99)
    assert cursor.calls[1][1] == ("ana@example.com", 99, 99)
    assert (connection.commits, connection.rollbacks) == (0, 1)
    assert (cursor.closed, connection.closed) == (1, 1)


@pytest.mark.parametrize(
    ("row", "expected", "commits", "rollbacks"),
    [
        (
            (8, "inactivo"),
            {"mensaje": "Estado de profesor actualizado", "id": 8, "estado": "inactivo"},
            1,
            0,
        ),
        (None, {"error": "Profesor no encontrado"}, 0, 1),
    ],
)
def test_actualizar_estado_normaliza_y_conserva_transaccion(
    monkeypatch,
    row,
    expected,
    commits,
    rollbacks,
):
    cursor = CursorProbe(fetchones=[row])
    connection, connections = _install_connection(monkeypatch, cursor)

    result = profesor_controller.actualizar_estado_profesor_controller(
        8,
        " InAcTiVo ",
    )

    assert result == expected
    assert len(connections) == 1
    assert len(cursor.calls) == 1
    assert _normalize_sql(cursor.calls[0][0]) == (
        "UPDATE profesor SET estado = %s WHERE id = %s "
        "RETURNING id, COALESCE(LOWER(estado), 'activo')"
    )
    assert cursor.calls[0][1] == ("inactivo", 8)
    assert (connection.commits, connection.rollbacks) == (commits, rollbacks)
    assert (cursor.closed, connection.closed) == (1, 1)
