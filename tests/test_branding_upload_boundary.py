import inspect
import threading
from collections import Counter
from contextlib import contextmanager
from io import BytesIO
from types import SimpleNamespace

import anyio
import pytest
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.routing import APIRoute
from starlette.datastructures import Headers

from app.controllers import branding_controller
from app.dependencies import get_current_active_admin, get_current_user
from app.globals import tenant_schema_var
from app.routes import branding as branding_routes


class ObservedUploadFile(UploadFile):
    def __init__(self, content, *, filename="logo.png", content_type="image/png", events=None):
        super().__init__(
            BytesIO(content),
            filename=filename,
            headers=Headers({"content-type": content_type}),
        )
        self.events = events

    async def read(self, size=-1):
        if self.events is not None:
            self.events.append(
                ("read", threading.get_ident(), tenant_schema_var.get())
            )
        return await super().read(size)


class CursorProbe:
    def __init__(self, previous_url, events):
        self.previous_url = previous_url
        self.events = events
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))
        operation = "select" if query.lstrip().startswith("SELECT") else "update"
        self.events.append(
            (operation, threading.get_ident(), tenant_schema_var.get())
        )

    def fetchone(self):
        if self.previous_url is None:
            return None
        return (self.previous_url,)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _upload_route():
    routes = [
        route
        for route in branding_routes.router.routes
        if isinstance(route, APIRoute) and route.path == "/branding/logo"
    ]
    post_routes = [route for route in routes if route.methods == {"POST"}]
    assert len(post_routes) == 1
    return post_routes[0]


def _upload_openapi():
    probe = FastAPI()
    probe.include_router(branding_routes.router)
    schema = probe.openapi()
    operation = schema["paths"]["/branding/logo"]["post"]
    body_schema = operation["requestBody"]["content"]["multipart/form-data"]["schema"]
    if "$ref" in body_schema:
        body_schema = schema["components"]["schemas"][body_schema["$ref"].split("/")[-1]]
    return operation, body_schema


def _install_sync_tail(
    monkeypatch,
    *,
    events,
    previous_url="/uploads/branding/tenant_demo/logo_viejo.png",
    slot="principal",
):
    cursors = []

    def fake_save_bytes(key, content, content_type):
        events.append(("save", threading.get_ident(), tenant_schema_var.get()))
        assert content == b"contenido"
        assert content_type == "image/png"
        assert key == f"branding/tenant_demo/logo_{slot}_fixed.png"

    def fake_storage_url(key):
        events.append(("url", threading.get_ident(), tenant_schema_var.get()))
        return f"/uploads/{key}"

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        assert commit is True
        cursor = CursorProbe(previous_url, events)
        cursors.append(cursor)
        events.append(("db_enter", threading.get_ident(), tenant_schema_var.get()))
        yield cursor
        events.append(("db_close", threading.get_ident(), tenant_schema_var.get()))

    def fake_delete_file(url):
        events.append(("delete", threading.get_ident(), tenant_schema_var.get()))
        assert url == previous_url

    monkeypatch.setattr(branding_controller, "save_bytes", fake_save_bytes)
    monkeypatch.setattr(branding_controller, "storage_url_for_key", fake_storage_url)
    monkeypatch.setattr(branding_controller, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(branding_controller, "delete_file", fake_delete_file)
    monkeypatch.setattr(
        branding_controller.uuid,
        "uuid4",
        lambda: SimpleNamespace(hex="fixed"),
    )
    return cursors


def test_upload_route_preserves_async_multipart_and_admin_dependencies():
    route = _upload_route()
    dependencies = Counter(dependency.dependency for dependency in route.dependencies)
    operation, body_schema = _upload_openapi()
    query_params = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }

    assert route.endpoint is branding_routes.subir_logo
    assert inspect.iscoroutinefunction(route.endpoint)
    assert inspect.iscoroutinefunction(branding_controller.subir_logo_controller)
    assert dependencies == Counter((get_current_user, get_current_active_admin))
    assert set(query_params) == {"slot"}
    assert query_params["slot"]["required"] is False
    assert query_params["slot"]["schema"]["type"] == "string"
    assert query_params["slot"]["schema"]["default"] == "principal"
    assert operation["requestBody"]["required"] is True
    assert set(body_schema["properties"]) == {"archivo"}
    assert body_schema["required"] == ["archivo"]
    assert body_schema["properties"]["archivo"]["type"] == "string"
    assert body_schema["properties"]["archivo"]["contentMediaType"] == (
        "application/octet-stream"
    )
    assert set(operation["responses"]) == {"200", "422"}


@pytest.mark.anyio
async def test_upload_route_awaits_controller_and_preserves_result(monkeypatch):
    upload = ObservedUploadFile(b"contenido")
    expected = {"url": "/uploads/logo.png", "slot": "secundario"}
    calls = []

    async def fake_controller(archivo, slot):
        calls.append((archivo, slot))
        return expected

    monkeypatch.setattr(branding_routes, "subir_logo_controller", fake_controller)
    try:
        result = await branding_routes.subir_logo(upload, "secundario")
    finally:
        await upload.close()

    assert result is expected
    assert calls == [(upload, "secundario")]


@pytest.mark.anyio
async def test_upload_route_preserves_controller_http_exception(monkeypatch):
    upload = ObservedUploadFile(b"contenido")
    expected = HTTPException(status_code=409, detail="conflicto")

    async def fake_controller(_archivo, _slot):
        raise expected

    monkeypatch.setattr(branding_routes, "subir_logo_controller", fake_controller)
    try:
        with pytest.raises(HTTPException) as excinfo:
            await branding_routes.subir_logo(upload, "principal")
    finally:
        await upload.close()

    assert excinfo.value is expected


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("slot", "column"),
    [
        ("principal", "logo_principal_url"),
        ("secundario", "logo_secundario_url"),
    ],
)
async def test_upload_preserves_read_storage_db_cleanup_order_and_payload(
    monkeypatch,
    slot,
    column,
):
    events = []
    previous_url = f"/uploads/branding/tenant_demo/logo_{slot}_viejo.png"
    cursors = _install_sync_tail(
        monkeypatch,
        events=events,
        previous_url=previous_url,
        slot=slot,
    )
    upload = ObservedUploadFile(b"contenido", events=events)
    token = tenant_schema_var.set("tenant_demo")
    try:
        result = await branding_controller.subir_logo_controller(upload, slot)
    finally:
        tenant_schema_var.reset(token)
        await upload.close()

    assert [event[0] for event in events] == [
        "read",
        "save",
        "url",
        "db_enter",
        "select",
        "update",
        "db_close",
        "delete",
    ]
    assert len(cursors) == 1
    assert column in cursors[0].calls[0][0]
    update_query, update_params = cursors[0].calls[1]
    assert column in update_query
    expected_url = f"/uploads/branding/tenant_demo/logo_{slot}_fixed.png"
    assert update_params == (expected_url,)
    assert result == {
        "url": expected_url,
        "slot": slot,
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("slot", "content_type", "filename", "content_size", "detail", "read_calls"),
    [
        (
            "lateral",
            "image/png",
            "logo.png",
            2,
            "slot debe ser 'principal' o 'secundario'",
            0,
        ),
        (
            "principal",
            "text/plain",
            "logo.png",
            2,
            "Tipo de archivo no permitido. Use: "
            f"{', '.join(branding_controller.ALLOWED_IMAGE_TYPES)}",
            0,
        ),
        (
            "principal",
            "image/png",
            "logo.gif",
            2,
            "Extension no permitida. Use: "
            f"{', '.join(branding_controller.ALLOWED_EXTENSIONS)}",
            0,
        ),
        (
            "principal",
            "image/png",
            "logo.png",
            branding_controller.MAX_LOGO_BYTES + 1,
            "Archivo demasiado grande (max 2048KB)",
            1,
        ),
    ],
    ids=("invalid-slot", "invalid-mime", "invalid-extension", "oversized"),
)
async def test_upload_validations_happen_before_sync_effects(
    monkeypatch,
    slot,
    content_type,
    filename,
    content_size,
    detail,
    read_calls,
):
    reads = []

    class ValidationUpload(ObservedUploadFile):
        async def read(self, size=-1):
            reads.append(size)
            return await super().read(size)

    def unexpected(*_args, **_kwargs):
        pytest.fail("No debe iniciar storage ni DB durante la validacion")

    for name in ("save_bytes", "storage_url_for_key", "get_cursor", "delete_file"):
        monkeypatch.setattr(branding_controller, name, unexpected)
    upload = ValidationUpload(
        b"x" * content_size,
        filename=filename,
        content_type=content_type,
    )
    try:
        with pytest.raises(HTTPException) as excinfo:
            await branding_controller.subir_logo_controller(upload, slot)
    finally:
        await upload.close()

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == detail
    assert len(reads) == read_calls


@pytest.mark.anyio
async def test_upload_read_failure_has_no_sync_effects(monkeypatch):
    effects = []

    class FailingUpload(ObservedUploadFile):
        async def read(self, size=-1):
            raise RuntimeError("fallo de lectura")

    for name in ("save_bytes", "storage_url_for_key", "get_cursor", "delete_file"):
        monkeypatch.setattr(
            branding_controller,
            name,
            lambda *_args, _name=name, **_kwargs: effects.append(_name),
        )
    upload = FailingUpload(b"contenido")
    try:
        with pytest.raises(RuntimeError, match="fallo de lectura"):
            await branding_controller.subir_logo_controller(upload, "principal")
    finally:
        await upload.close()

    assert effects == []


@pytest.mark.anyio
async def test_upload_storage_failure_does_not_open_db(monkeypatch):
    events = []

    def fail_save(*_args, **_kwargs):
        events.append("save")
        raise RuntimeError("fallo de storage")

    def unexpected_db(*_args, **_kwargs):
        pytest.fail("No debe abrir DB si storage falla")

    monkeypatch.setattr(branding_controller, "save_bytes", fail_save)
    for name in ("storage_url_for_key", "get_cursor", "delete_file"):
        monkeypatch.setattr(branding_controller, name, unexpected_db)
    upload = ObservedUploadFile(b"contenido")
    token = tenant_schema_var.set("tenant_demo")
    try:
        with pytest.raises(RuntimeError, match="fallo de storage"):
            await branding_controller.subir_logo_controller(upload, "principal")
    finally:
        tenant_schema_var.reset(token)
        await upload.close()

    assert events == ["save"]


@pytest.mark.anyio
async def test_upload_db_failure_keeps_existing_no_compensation_behavior(monkeypatch):
    events = []

    monkeypatch.setattr(
        branding_controller,
        "save_bytes",
        lambda *_args, **_kwargs: events.append("save"),
    )
    monkeypatch.setattr(
        branding_controller,
        "storage_url_for_key",
        lambda _key: "/uploads/logo_nuevo.png",
    )

    @contextmanager
    def failing_cursor(commit=False, cursor_factory=None):
        assert commit is True
        events.append("db")
        raise RuntimeError("fallo de DB")
        yield

    monkeypatch.setattr(branding_controller, "get_cursor", failing_cursor)
    monkeypatch.setattr(
        branding_controller,
        "delete_file",
        lambda _url: events.append("delete"),
    )
    upload = ObservedUploadFile(b"contenido")
    token = tenant_schema_var.set("tenant_demo")
    try:
        with pytest.raises(RuntimeError, match="fallo de DB"):
            await branding_controller.subir_logo_controller(upload, "principal")
    finally:
        tenant_schema_var.reset(token)
        await upload.close()

    assert events == ["save", "db"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "previous_url",
    [None, "/uploads/branding/tenant_demo/logo_principal_fixed.png"],
)
async def test_upload_does_not_delete_when_previous_logo_is_absent_or_unchanged(
    monkeypatch,
    previous_url,
):
    events = []
    _install_sync_tail(monkeypatch, events=events, previous_url=previous_url)
    upload = ObservedUploadFile(b"contenido", events=events)
    token = tenant_schema_var.set("tenant_demo")
    try:
        await branding_controller.subir_logo_controller(upload, "principal")
    finally:
        tenant_schema_var.reset(token)
        await upload.close()

    assert "delete" not in [event[0] for event in events]


@pytest.mark.anyio
async def test_upload_cancellation_during_async_read_has_no_effects(monkeypatch):
    read_started = anyio.Event()
    effects = []

    class BlockingReadUpload(ObservedUploadFile):
        async def read(self, size=-1):
            read_started.set()
            await anyio.sleep_forever()

    for name in ("save_bytes", "storage_url_for_key", "get_cursor", "delete_file"):
        monkeypatch.setattr(
            branding_controller,
            name,
            lambda *_args, _name=name, **_kwargs: effects.append(_name),
        )
    upload = BlockingReadUpload(b"contenido")

    async def call_controller():
        await branding_controller.subir_logo_controller(upload, "principal")

    try:
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(call_controller)
            await read_started.wait()
            task_group.cancel_scope.cancel()
    finally:
        await upload.close()

    assert effects == []


@pytest.mark.anyio
async def test_upload_sync_tail_runs_in_real_workers_with_isolated_tenants(monkeypatch):
    tenants = ("tenant_alpha", "tenant_beta")
    loop_thread = threading.get_ident()
    entered = threading.Barrier(2)
    sampled = threading.Barrier(2)
    lock = threading.Lock()
    observations = {tenant: [] for tenant in tenants}
    results = {}

    def record(operation):
        tenant = tenant_schema_var.get()
        observation = (operation, threading.get_ident(), tenant)
        with lock:
            observations[tenant].append(observation)

    def fake_save(key, content, content_type):
        tenant = tenant_schema_var.get()
        assert key == f"branding/{tenant}/logo_principal_fixed.png"
        assert content == b"contenido"
        assert content_type == "image/png"
        record("save")
        entered.wait(timeout=3)
        record("overlap")
        sampled.wait(timeout=3)

    def fake_url(key):
        record("url")
        return f"/uploads/{key}"

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        assert commit is True
        tenant = tenant_schema_var.get()
        record("db_enter")
        cursor = CursorProbe(f"/uploads/branding/{tenant}/viejo.png", [])
        yield cursor
        record("db_close")

    def fake_delete(_url):
        record("delete")

    monkeypatch.setattr(branding_controller, "save_bytes", fake_save)
    monkeypatch.setattr(branding_controller, "storage_url_for_key", fake_url)
    monkeypatch.setattr(branding_controller, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(branding_controller, "delete_file", fake_delete)
    monkeypatch.setattr(
        branding_controller.uuid,
        "uuid4",
        lambda: SimpleNamespace(hex="fixed"),
    )

    async def run_upload(tenant):
        read_events = []
        upload = ObservedUploadFile(b"contenido", events=read_events)
        token = tenant_schema_var.set(tenant)
        try:
            results[tenant] = await branding_controller.subir_logo_controller(
                upload,
                "principal",
            )
        finally:
            tenant_schema_var.reset(token)
            await upload.close()
        assert read_events == [("read", loop_thread, tenant)]

    try:
        with anyio.fail_after(5):
            async with anyio.create_task_group() as task_group:
                for tenant in tenants:
                    task_group.start_soon(run_upload, tenant)
    finally:
        entered.abort()
        sampled.abort()

    worker_threads = set()
    for tenant in tenants:
        tenant_observations = observations[tenant]
        assert [item[0] for item in tenant_observations] == [
            "save",
            "overlap",
            "url",
            "db_enter",
            "db_close",
            "delete",
        ]
        assert {item[2] for item in tenant_observations} == {tenant}
        request_threads = {item[1] for item in tenant_observations}
        assert len(request_threads) == 1
        worker_threads.update(request_threads)
        assert results[tenant] == {
            "url": f"/uploads/branding/{tenant}/logo_principal_fixed.png",
            "slot": "principal",
        }

    assert len(worker_threads) == 2
    assert loop_thread not in worker_threads


async def _wait_for_thread_event(event):
    with anyio.fail_after(3):
        while not event.is_set():
            await anyio.sleep(0)


@pytest.mark.anyio
async def test_upload_worker_cancellation_waits_for_db_and_cleanup(monkeypatch):
    worker_started = threading.Event()
    allow_worker_to_finish = threading.Event()
    worker_finished = threading.Event()
    caller_finished = anyio.Event()
    cancellation_delivered = anyio.Event()
    events = []

    def blocking_save(*_args, **_kwargs):
        worker_started.set()
        if not allow_worker_to_finish.wait(timeout=3):
            raise TimeoutError("branding worker timed out")
        events.append("save")

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        assert commit is True
        events.append("db")
        yield CursorProbe("/uploads/logo_viejo.png", [])
        events.append("db_close")

    def fake_delete(_url):
        events.append("delete")
        worker_finished.set()

    monkeypatch.setattr(branding_controller, "save_bytes", blocking_save)
    monkeypatch.setattr(
        branding_controller,
        "storage_url_for_key",
        lambda _key: "/uploads/logo_nuevo.png",
    )
    monkeypatch.setattr(branding_controller, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(branding_controller, "delete_file", fake_delete)
    upload = ObservedUploadFile(b"contenido")

    async def call_controller():
        try:
            await branding_controller.subir_logo_controller(upload, "principal")
        finally:
            caller_finished.set()

    async def cancellation_sentinel():
        try:
            await anyio.sleep_forever()
        finally:
            cancellation_delivered.set()

    async def run_cancelled_group(*, task_status=anyio.TASK_STATUS_IGNORED):
        with anyio.CancelScope() as cancel_scope:
            async with anyio.create_task_group() as inner_group:
                task_status.started(cancel_scope)
                inner_group.start_soon(call_controller)
                inner_group.start_soon(cancellation_sentinel)

    try:
        async with anyio.create_task_group() as task_group:
            cancel_scope = await task_group.start(run_cancelled_group)
            await _wait_for_thread_event(worker_started)
            cancel_scope.cancel()
            with anyio.fail_after(3):
                await cancellation_delivered.wait()

            assert not caller_finished.is_set()
            assert not worker_finished.is_set()
            allow_worker_to_finish.set()
    finally:
        allow_worker_to_finish.set()
        await upload.close()

    assert events == ["save", "db", "db_close", "delete"]
    assert worker_finished.is_set()
    assert caller_finished.is_set()
