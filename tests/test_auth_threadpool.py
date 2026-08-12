import threading

import anyio
import pytest
from fastapi import HTTPException

from app import dependencies, main as app_main
from app.core import super_admin
from app.globals import tenant_schema_var
from app.security import create_access_token


class CookieRequest:
    def __init__(self, token):
        self.cookies = {"token": token}
        self.headers = {}


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _token(tenant="tenant_demo", role="admin", user_id="9"):
    return create_access_token({"sub": user_id, "rol": role, "tenant": tenant})


async def _wait_for_thread_event(event):
    with anyio.fail_after(3):
        while not event.is_set():
            await anyio.sleep(0)


@pytest.mark.anyio
async def test_cookie_auth_threadpool_preserves_tenants_and_middleware_cleanup(monkeypatch):
    tenants = ("tenant_alpha", "tenant_beta")
    status_gate = threading.Barrier(2)
    validation_gate = threading.Barrier(2)
    loop_thread = threading.get_ident()
    observations = {}
    results = {}
    lock = threading.Lock()

    def fake_ensure_tenant(tenant):
        before = tenant_schema_var.get()
        public_token = tenant_schema_var.set("public")
        try:
            observation = {
                "thread": threading.get_ident(),
                "before": before,
                "during": tenant_schema_var.get(),
            }
            status_gate.wait(timeout=3)
        finally:
            tenant_schema_var.reset(public_token)
        observation["after"] = tenant_schema_var.get()
        with lock:
            observations[(tenant, "status")] = observation
        return {"tenant": tenant, "estado": "activo"}

    def fake_validate_user(user_id, role):
        tenant = tenant_schema_var.get()
        observation = {
            "thread": threading.get_ident(),
            "tenant": tenant,
            "user_id": user_id,
            "role": role,
        }
        validation_gate.wait(timeout=3)
        with lock:
            observations[(tenant, "validation")] = observation

    monkeypatch.setattr(
        dependencies,
        "ensure_tenant_allowed_for_app",
        fake_ensure_tenant,
    )
    monkeypatch.setattr(
        dependencies,
        "_validar_usuario_en_bd",
        fake_validate_user,
    )

    async def run_request(tenant):
        request = CookieRequest(_token(tenant=tenant))

        async def call_next(received_request):
            assert received_request is request
            downstream_entry = tenant_schema_var.get()
            user = await dependencies.get_current_user(request, token=None)
            return {
                "downstream_entry": downstream_entry,
                "after_auth": tenant_schema_var.get(),
                "user": user,
            }

        before = tenant_schema_var.get()
        downstream = await app_main.tenant_middleware(request, call_next)
        results[tenant] = {
            "before": before,
            "downstream": downstream,
            "after": tenant_schema_var.get(),
        }

    original = tenant_schema_var.get()
    outer_token = tenant_schema_var.set("tenant_outer")
    try:
        try:
            with anyio.fail_after(5):
                async with anyio.create_task_group() as task_group:
                    for tenant in tenants:
                        task_group.start_soon(run_request, tenant)
            restored_outer = tenant_schema_var.get()
        finally:
            status_gate.abort()
            validation_gate.abort()
    finally:
        tenant_schema_var.reset(outer_token)

    assert restored_outer == "tenant_outer"
    assert tenant_schema_var.get() == original
    assert len({observations[(tenant, "status")]["thread"] for tenant in tenants}) == 2
    assert len({observations[(tenant, "validation")]["thread"] for tenant in tenants}) == 2

    for tenant in tenants:
        status_observation = observations[(tenant, "status")]
        validation_observation = observations[(tenant, "validation")]
        result = results[tenant]

        assert status_observation == {
            "thread": status_observation["thread"],
            "before": None,
            "during": "public",
            "after": None,
        }
        assert status_observation["thread"] != loop_thread
        assert validation_observation == {
            "thread": validation_observation["thread"],
            "tenant": tenant,
            "user_id": 9,
            "role": "admin",
        }
        assert validation_observation["thread"] != loop_thread
        assert result == {
            "before": "tenant_outer",
            "downstream": {
                "downstream_entry": None,
                "after_auth": tenant,
                "user": {"id": 9, "rol": "admin", "tenant": tenant},
            },
            "after": "tenant_outer",
        }


@pytest.mark.anyio
async def test_bearer_middleware_context_is_restored_inside_tenant_status_worker(
    monkeypatch,
):
    tenant = "tenant_bearer"
    loop_thread = threading.get_ident()
    observations = []

    def fake_ensure_tenant(received_tenant):
        before = tenant_schema_var.get()
        public_token = tenant_schema_var.set("public")
        try:
            during = tenant_schema_var.get()
        finally:
            tenant_schema_var.reset(public_token)
        observations.append(
            {
                "thread": threading.get_ident(),
                "tenant": received_tenant,
                "before": before,
                "during": during,
                "after": tenant_schema_var.get(),
            }
        )

    monkeypatch.setattr(
        dependencies,
        "ensure_tenant_allowed_for_app",
        fake_ensure_tenant,
    )
    monkeypatch.setattr(dependencies, "_validar_usuario_en_bd", lambda *_args: None)

    token = _token(tenant=tenant)
    request = CookieRequest(token)
    request.headers = {"Authorization": f"Bearer {token}"}
    original = tenant_schema_var.get()
    outer_token = tenant_schema_var.set("tenant_outer")
    try:
        async def call_next(received_request):
            assert received_request is request
            assert tenant_schema_var.get() == tenant
            user = await dependencies.get_current_user(request, token=token)
            return {"user": user, "after_auth": tenant_schema_var.get()}

        response = await app_main.tenant_middleware(request, call_next)
        after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer_token)

    assert observations == [
        {
            "thread": observations[0]["thread"],
            "tenant": tenant,
            "before": tenant,
            "during": "public",
            "after": tenant,
        }
    ]
    assert observations[0]["thread"] != loop_thread
    assert response == {
        "user": {"id": 9, "rol": "admin", "tenant": tenant},
        "after_auth": tenant,
    }
    assert after == "tenant_outer"
    assert tenant_schema_var.get() == original


@pytest.mark.anyio
async def test_auth_threadpool_keeps_tenant_set_between_separate_offloads(monkeypatch):
    calls = []

    async def fake_run_in_threadpool(function, *args):
        calls.append(("offload", function.__name__, tenant_schema_var.get(), args))
        return function(*args)

    def fake_ensure_tenant(tenant):
        calls.append(("status", tenant, tenant_schema_var.get()))

    def fake_validate_user(user_id, role):
        calls.append(("validation", user_id, role, tenant_schema_var.get()))

    monkeypatch.setattr(dependencies, "run_in_threadpool", fake_run_in_threadpool)
    monkeypatch.setattr(
        dependencies,
        "ensure_tenant_allowed_for_app",
        fake_ensure_tenant,
    )
    monkeypatch.setattr(
        dependencies,
        "_validar_usuario_en_bd",
        fake_validate_user,
    )

    original = tenant_schema_var.get()
    outer_token = tenant_schema_var.set("tenant_outer")
    try:
        user = await dependencies.get_current_user(
            CookieRequest(_token()),
            token=None,
        )
        after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer_token)

    assert user == {"id": 9, "rol": "admin", "tenant": "tenant_demo"}
    assert after == "tenant_demo"
    assert tenant_schema_var.get() == original
    assert calls == [
        (
            "offload",
            "fake_ensure_tenant",
            "tenant_outer",
            ("tenant_demo",),
        ),
        ("status", "tenant_demo", "tenant_outer"),
        (
            "offload",
            "fake_validate_user",
            "tenant_demo",
            (9, "admin"),
        ),
        ("validation", 9, "admin", "tenant_demo"),
    ]


@pytest.mark.anyio
async def test_suspended_tenant_keeps_403_and_skips_user_validation(monkeypatch):
    expected = HTTPException(status_code=403, detail="Tenant no autorizado")

    def reject_tenant(_tenant):
        raise expected

    monkeypatch.setattr(dependencies, "ensure_tenant_allowed_for_app", reject_tenant)
    monkeypatch.setattr(
        dependencies,
        "_validar_usuario_en_bd",
        lambda *_args: pytest.fail("No debe validar al usuario tras un 403 del tenant"),
    )

    original = tenant_schema_var.get()
    outer_token = tenant_schema_var.set("tenant_outer")
    try:
        with pytest.raises(HTTPException) as exc:
            await dependencies.get_current_user(CookieRequest(_token()), token=None)
        after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer_token)

    assert exc.value is expected
    assert exc.value.status_code == 403
    assert exc.value.detail == "Tenant no autorizado"
    assert after == "tenant_outer"
    assert tenant_schema_var.get() == original


@pytest.mark.anyio
async def test_invalid_tenant_user_keeps_canonical_401(monkeypatch):
    monkeypatch.setattr(
        dependencies,
        "ensure_tenant_allowed_for_app",
        lambda _tenant: {"estado": "activo"},
    )
    monkeypatch.setattr(
        dependencies,
        "_validar_usuario_en_bd",
        lambda *_args: (_ for _ in ()).throw(ValueError("Usuario no valido")),
    )

    original = tenant_schema_var.get()
    outer_token = tenant_schema_var.set("tenant_outer")
    try:
        with pytest.raises(HTTPException) as exc:
            await dependencies.get_current_user(CookieRequest(_token()), token=None)
        after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer_token)

    assert exc.value.status_code == 401
    assert exc.value.detail == "No se pudo validar las credenciales"
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}
    assert after == "tenant_demo"
    assert tenant_schema_var.get() == original


@pytest.mark.anyio
async def test_unexpected_tenant_database_error_is_not_reclassified(monkeypatch):
    expected = RuntimeError("database unavailable")
    monkeypatch.setattr(
        dependencies,
        "ensure_tenant_allowed_for_app",
        lambda _tenant: {"estado": "activo"},
    )

    def fail_validation(*_args):
        raise expected

    monkeypatch.setattr(dependencies, "_validar_usuario_en_bd", fail_validation)

    original = tenant_schema_var.get()
    outer_token = tenant_schema_var.set("tenant_outer")
    try:
        with pytest.raises(RuntimeError) as exc:
            await dependencies.get_current_user(CookieRequest(_token()), token=None)
        after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer_token)

    assert exc.value is expected
    assert after == "tenant_demo"
    assert tenant_schema_var.get() == original


@pytest.mark.anyio
async def test_super_admin_validation_threadpool_uses_public_without_caller_leak(monkeypatch):
    loop_thread = threading.get_ident()
    observations = []

    class Cursor:
        def execute(self, query, params):
            observations.append(
                ("execute", threading.get_ident(), tenant_schema_var.get(), query, params)
            )

        def fetchone(self):
            return ("activo",)

        def close(self):
            observations.append(("cursor_close", tenant_schema_var.get()))

    class Connection:
        def cursor(self):
            return Cursor()

        def close(self):
            observations.append(("connection_close", tenant_schema_var.get()))

    monkeypatch.setattr(super_admin, "get_connection", Connection)

    original = tenant_schema_var.get()
    outer_token = tenant_schema_var.set("tenant_outer")
    try:
        user = await super_admin.get_current_super_admin(
            CookieRequest(_token(tenant="public", role="super_admin", user_id="7")),
            token=None,
        )
        after = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(outer_token)

    execute = observations[0]
    assert execute[0] == "execute"
    assert execute[1] != loop_thread
    assert execute[2] == "public"
    assert "FROM public.super_admins" in execute[3]
    assert execute[4] == (7,)
    assert observations[1:] == [
        ("cursor_close", "public"),
        ("connection_close", "public"),
    ]
    assert user == {"id": 7, "rol": "super_admin", "tenant": "public"}
    assert after == "tenant_outer"
    assert tenant_schema_var.get() == original


@pytest.mark.anyio
async def test_inactive_super_admin_keeps_canonical_401(monkeypatch):
    monkeypatch.setattr(
        super_admin,
        "validate_super_admin",
        lambda _user_id: (_ for _ in ()).throw(ValueError("Super admin no valido")),
    )

    with pytest.raises(HTTPException) as exc:
        await super_admin.get_current_super_admin(
            CookieRequest(_token(tenant="public", role="super_admin", user_id="7")),
            token=None,
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "No se pudo validar las credenciales"
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.anyio
async def test_unexpected_super_admin_database_error_is_not_reclassified(monkeypatch):
    expected = RuntimeError("database unavailable")

    def fail_validation(_user_id):
        raise expected

    monkeypatch.setattr(super_admin, "validate_super_admin", fail_validation)

    with pytest.raises(RuntimeError) as exc:
        await super_admin.get_current_super_admin(
            CookieRequest(_token(tenant="public", role="super_admin", user_id="7")),
            token=None,
        )

    assert exc.value is expected


@pytest.mark.anyio
@pytest.mark.parametrize("boundary", ["tenant_status", "user_validation", "super_admin"])
async def test_auth_threadpool_cancellation_waits_for_boundary_cleanup(monkeypatch, boundary):
    worker_started = threading.Event()
    release_worker = threading.Event()
    worker_finished = threading.Event()
    caller_finished = anyio.Event()
    cancellation_delivered = anyio.Event()
    loop_thread = threading.get_ident()
    worker_threads = []

    def blocking_boundary(*_args):
        worker_threads.append(threading.get_ident())
        worker_started.set()
        try:
            if not release_worker.wait(timeout=3):
                raise TimeoutError("auth boundary test timed out")
        finally:
            worker_finished.set()

    if boundary == "tenant_status":
        monkeypatch.setattr(
            dependencies,
            "ensure_tenant_allowed_for_app",
            blocking_boundary,
        )
        monkeypatch.setattr(dependencies, "_validar_usuario_en_bd", lambda *_args: None)

        async def invoke_dependency():
            await dependencies.get_current_user(CookieRequest(_token()), token=None)

    elif boundary == "user_validation":
        monkeypatch.setattr(
            dependencies,
            "ensure_tenant_allowed_for_app",
            lambda _tenant: {"estado": "activo"},
        )
        monkeypatch.setattr(dependencies, "_validar_usuario_en_bd", blocking_boundary)

        async def invoke_dependency():
            await dependencies.get_current_user(CookieRequest(_token()), token=None)

    else:
        monkeypatch.setattr(super_admin, "validate_super_admin", blocking_boundary)

        async def invoke_dependency():
            await super_admin.get_current_super_admin(
                CookieRequest(
                    _token(tenant="public", role="super_admin", user_id="7")
                ),
                token=None,
            )

    async def call_dependency():
        try:
            await invoke_dependency()
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
                inner_group.start_soon(call_dependency)
                inner_group.start_soon(cancellation_sentinel)

    try:
        async with anyio.create_task_group() as task_group:
            cancel_scope = await task_group.start(run_cancelled_group)
            await _wait_for_thread_event(worker_started)

            cancel_scope.cancel()
            with anyio.fail_after(3):
                await cancellation_delivered.wait()

            assert not worker_finished.is_set()
            assert not caller_finished.is_set()
            release_worker.set()
    finally:
        release_worker.set()

    assert worker_finished.is_set()
    assert caller_finished.is_set()
    assert worker_threads and all(thread != loop_thread for thread in worker_threads)
