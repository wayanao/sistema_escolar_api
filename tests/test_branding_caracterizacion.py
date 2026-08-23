"""Caracterización de la frontera completa de branding para la subcapa 7.0.

Complementa las pruebas heredadas de la capa 1 y de concurrencia. Fija la
frontera, los contratos HTTP que no cubría el upload, los conteos de recursos y
varios comportamientos heredados que esta capa registra sin corregir.
"""

import ast
import inspect
import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

from app import main
from app.controllers import branding_controller
from app.dependencies import get_current_active_admin, get_current_user
from app.routes import branding as branding_routes
from app.schemas.branding import BrandingUpdate
from app.services import storage


ROOT = Path(__file__).resolve().parents[1]
BRANDING_PRODUCT_FILES = {
    "app/routes/branding.py": 36,
    "app/controllers/branding_controller.py": 181,
    "app/schemas/branding.py": 29,
}
FULL_ROW = (
    1,
    "Colegio",
    "Lema",
    "/uploads/branding/tenant_demo/principal.png",
    "/uploads/branding/tenant_demo/secundario.png",
    "Calle 1",
    "555",
    "info@colegio.edu",
    "900",
    "12345",
    "colegio.edu",
    "#111111",
    "#222222",
    {"clave": "valor"},
)
EMPTY_ROW = (
    2,
    "",
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)


class CursorProbe:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class CursorContexts:
    def __init__(self, rows_by_connection):
        self.rows_by_connection = list(rows_by_connection)
        self.cursors = []
        self.commits = []

    @contextmanager
    def open(self, commit=False, cursor_factory=None):
        del cursor_factory
        rows = self.rows_by_connection.pop(0)
        cursor = CursorProbe(rows)
        self.cursors.append(cursor)
        self.commits.append(commit)
        yield cursor

    @property
    def query_count(self):
        return sum(len(cursor.calls) for cursor in self.cursors)


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


def _branding_routes():
    return {
        (next(iter(route.methods)), route.path): route
        for route in branding_routes.router.routes
        if isinstance(route, APIRoute)
    }


def _probe_app(user):
    probe = FastAPI()
    probe.include_router(branding_routes.router)

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
    start = next(message for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body) if response_body else None


def test_frontera_archivos_sql_y_consumidores_queda_fijada():
    assert {
        path: len(_source(path).splitlines())
        for path in BRANDING_PRODUCT_FILES
    } == BRANDING_PRODUCT_FILES
    assert _execute_count("app/routes/branding.py") == 0
    assert _execute_count("app/controllers/branding_controller.py") == 7
    assert _execute_count("app/schemas/branding.py") == 0
    assert not (ROOT / "app/repositories/branding_repository.py").exists()

    table_consumers = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "app").rglob("*.py")
        if "institucion_branding" in path.read_text(encoding="utf-8")
    }
    assert table_consumers == {
        "app/controllers/branding_controller.py",
        "app/controllers/super_admin_controller.py",
    }


def test_storage_es_compartido_solo_por_los_consumidores_registrados():
    consumers = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "app").rglob("*.py")
        if "from app.services.storage import" in path.read_text(encoding="utf-8")
    }
    assert consumers == {
        "app/controllers/branding_controller.py",
        "app/controllers/plan_de_clases_controller.py",
        "app/main.py",
    }


def test_rutas_metodos_permisos_sync_y_response_model_quedan_fijados():
    routes = _branding_routes()
    assert set(routes) == {
        ("GET", "/branding"),
        ("PUT", "/branding"),
        ("POST", "/branding/logo"),
        ("DELETE", "/branding/logo"),
    }

    for key, route in routes.items():
        dependencies = [dependency.dependency for dependency in route.dependencies]
        assert dependencies[0] is get_current_user
        if key[0] == "GET":
            assert dependencies == [get_current_user]
        else:
            assert dependencies == [get_current_user, get_current_active_admin]
        assert route.response_model is None

    assert inspect.iscoroutinefunction(routes[("POST", "/branding/logo")].endpoint)
    assert not inspect.iscoroutinefunction(routes[("GET", "/branding")].endpoint)
    assert not inspect.iscoroutinefunction(routes[("PUT", "/branding")].endpoint)
    assert not inspect.iscoroutinefunction(routes[("DELETE", "/branding/logo")].endpoint)


@pytest.mark.anyio
async def test_get_http_permite_profesor_y_conserva_payload(monkeypatch):
    expected = {
        "id": 1,
        "nombre_institucion": "Colegio",
        "eslogan": "Lema",
        "logo_principal_url": None,
        "logo_secundario_url": None,
        "direccion": "",
        "telefono": "",
        "email": "",
        "nit": "",
        "codigo_dane": "",
        "sitio_web": "",
        "color_primario": "#0f314f",
        "color_secundario": "#526775",
        "configuracion_extra": {},
    }
    monkeypatch.setattr(
        branding_routes,
        "obtener_branding_controller",
        lambda: expected,
    )
    app = _probe_app({"id": 7, "rol": "profesor", "tenant": "tenant_demo"})

    status_code, body = await _asgi_request(app, "GET", "/branding")

    assert status_code == 200
    assert body == expected


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("role", "expected_status"),
    [("admin", 200), ("profesor", 403)],
)
async def test_put_http_exige_admin_activo(monkeypatch, role, expected_status):
    calls = []

    def fake_update(data):
        calls.append(data)
        return {"nombre_institucion": data.nombre_institucion}

    monkeypatch.setattr(branding_routes, "actualizar_branding_controller", fake_update)
    app = _probe_app({"id": 7, "rol": role, "tenant": "tenant_demo"})

    status_code, body = await _asgi_request(
        app,
        "PUT",
        "/branding",
        json_body={"nombre_institucion": "Colegio"},
    )

    assert status_code == expected_status
    if role == "admin":
        assert body == {"nombre_institucion": "Colegio"}
        assert len(calls) == 1
    else:
        assert body == {"detail": "No tienes los permisos necesarios"}
        assert calls == []


@pytest.mark.anyio
async def test_put_http_con_configuracion_no_objeto_responde_422(monkeypatch):
    monkeypatch.setattr(
        branding_routes,
        "actualizar_branding_controller",
        lambda _data: pytest.fail("La validación debe ocurrir antes del controlador"),
    )
    app = _probe_app({"id": 7, "rol": "admin", "tenant": "tenant_demo"})

    status_code, body = await _asgi_request(
        app,
        "PUT",
        "/branding",
        json_body={"configuracion_extra": []},
    )

    assert status_code == 422
    assert body["detail"][0]["loc"] == ["body", "configuracion_extra"]


@pytest.mark.anyio
async def test_delete_http_slot_invalido_responde_400_sin_db(monkeypatch):
    monkeypatch.setattr(
        branding_controller,
        "get_cursor",
        lambda *_args, **_kwargs: pytest.fail("No debe abrir DB"),
    )
    app = _probe_app({"id": 7, "rol": "admin", "tenant": "tenant_demo"})

    status_code, body = await _asgi_request(
        app,
        "DELETE",
        "/branding/logo?slot=lateral",
    )

    assert status_code == 400
    assert body == {"detail": "slot debe ser 'principal' o 'secundario'"}


def test_esquema_acepta_nulos_y_textos_sin_validacion_de_formato_o_longitud():
    data = BrandingUpdate(
        nombre_institucion=None,
        email="no-es-un-email",
        color_primario="sin-formato",
        color_secundario="x" * 4000,
        configuracion_extra=None,
    )

    assert data.nombre_institucion is None
    assert data.email == "no-es-un-email"
    assert data.color_primario == "sin-formato"
    assert len(data.color_secundario) == 4000
    assert data.configuracion_extra is None


@pytest.mark.parametrize(
    ("rows", "expected_queries"),
    [([FULL_ROW], 1), ([None, EMPTY_ROW], 2)],
    ids=("existing-row", "implicit-create"),
)
def test_get_usa_una_conexion_transaccional_y_puede_escribir(
    monkeypatch,
    rows,
    expected_queries,
):
    contexts = CursorContexts([rows])
    monkeypatch.setattr(branding_controller, "get_cursor", contexts.open)

    branding_controller.obtener_branding_controller()

    assert contexts.commits == [True]
    assert len(contexts.cursors) == 1
    assert contexts.query_count == expected_queries


def test_put_confirma_y_relee_en_una_segunda_conexion(monkeypatch):
    contexts = CursorContexts([[], [FULL_ROW]])
    monkeypatch.setattr(branding_controller, "get_cursor", contexts.open)
    data = BrandingUpdate(nombre_institucion="Nuevo")

    result = branding_controller.actualizar_branding_controller(data)

    assert contexts.commits == [True, True]
    assert len(contexts.cursors) == 2
    assert contexts.query_count == 2
    assert result["nombre_institucion"] == "Colegio"


def test_put_sin_fila_pierde_los_valores_y_devuelve_la_fila_por_defecto(monkeypatch):
    contexts = CursorContexts([[], [None, EMPTY_ROW]])
    monkeypatch.setattr(branding_controller, "get_cursor", contexts.open)

    result = branding_controller.actualizar_branding_controller(
        BrandingUpdate(nombre_institucion="Nuevo")
    )

    assert contexts.commits == [True, True]
    assert contexts.query_count == 3
    assert result["id"] == 2
    assert result["nombre_institucion"] == ""


def test_upload_sin_fila_guarda_archivo_y_responde_exito_sin_asociarlo(
    monkeypatch,
):
    contexts = CursorContexts([[None]])
    saved = []
    deleted = []
    monkeypatch.setattr(branding_controller, "get_cursor", contexts.open)
    monkeypatch.setattr(
        branding_controller,
        "save_bytes",
        lambda key, content, content_type: saved.append((key, content, content_type)),
    )
    monkeypatch.setattr(
        branding_controller,
        "storage_url_for_key",
        lambda key: f"/uploads/{key}",
    )
    monkeypatch.setattr(branding_controller, "delete_file", deleted.append)
    monkeypatch.setattr(
        branding_controller.uuid,
        "uuid4",
        lambda: SimpleNamespace(hex="fixed"),
    )
    token = branding_controller.tenant_schema_var.set("tenant_demo")
    try:
        result = branding_controller._guardar_logo_leido(
            b"contenido",
            "image/png",
            "principal",
            ".png",
        )
    finally:
        branding_controller.tenant_schema_var.reset(token)

    expected_url = "/uploads/branding/tenant_demo/logo_principal_fixed.png"
    assert contexts.commits == [True]
    assert contexts.query_count == 2
    assert saved == [
        ("branding/tenant_demo/logo_principal_fixed.png", b"contenido", "image/png")
    ]
    assert deleted == []
    assert result == {"url": expected_url, "slot": "principal"}


def test_delete_sin_fila_responde_exito_y_solicita_borrar_none(monkeypatch):
    contexts = CursorContexts([[None]])
    deleted = []
    monkeypatch.setattr(branding_controller, "get_cursor", contexts.open)
    monkeypatch.setattr(branding_controller, "delete_file", deleted.append)

    result = branding_controller.eliminar_logo_controller("principal")

    assert contexts.commits == [True]
    assert contexts.query_count == 2
    assert deleted == [None]
    assert result == {"mensaje": "Logo eliminado", "slot": "principal"}


def test_no_hay_n_mas_uno_de_aplicacion_y_los_conteos_son_constantes():
    tree = ast.parse(_source("app/controllers/branding_controller.py"))
    assert not any(isinstance(node, (ast.For, ast.AsyncFor, ast.While)) for node in ast.walk(tree))


def test_ddl_no_impone_una_sola_fila_y_deja_campos_de_negocio_nullable():
    base = _source("migrations/base/20260813_esquema_base_tenant.sql")
    table_block = base.split("CREATE TABLE IF NOT EXISTS institucion_branding (", 1)[1]
    table_block = table_block.split("CREATE TABLE IF NOT EXISTS inventario (", 1)[0]
    incremental = _source("migrations/20260509_branding_plantillas_impresion.sql")

    assert "UNIQUE" not in table_block
    assert "WHERE NOT EXISTS (SELECT 1 FROM institucion_branding)" in incremental
    assert "nombre_institucion character varying(255) DEFAULT" in table_block
    assert "nombre_institucion character varying(255) NOT NULL" not in table_block
    assert "codigo_dane character varying(20) DEFAULT" in table_block
    assert "codigo_dane character varying(20) NOT NULL" not in table_block


def test_borrado_remoto_absorbe_fallo_del_proveedor(monkeypatch):
    class FailingClient:
        def delete_object(self, **_kwargs):
            raise RuntimeError("fallo remoto")

    monkeypatch.setattr(storage, "using_remote_storage", lambda: True)
    monkeypatch.setattr(storage, "_remote_client", FailingClient)

    assert storage.delete_file("/uploads/branding/tenant_demo/logo.png") is None


def test_upload_ajeno_inexistente_responde_404_antes_de_autorizar(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UPLOADS_ROOT", tmp_path.resolve())
    monkeypatch.setattr(main, "using_remote_storage", lambda: False)

    with pytest.raises(Exception) as excinfo:
        main._validar_acceso_archivo_upload(
            "branding/tenant_otro/no-existe.png",
            {"id": 7, "rol": "profesor", "tenant": "tenant_demo"},
        )

    assert excinfo.value.status_code == 404
