import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import anyio
import pytest
from starlette.concurrency import run_in_threadpool

from app import dependencies, main as app_main
from app.globals import tenant_schema_var
from app.security import create_access_token


class CookieRequest:
    def __init__(self, token):
        self.cookies = {"token": token}
        self.headers = {}


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _wait_for_thread_event(event):
    with anyio.fail_after(3):
        while not event.is_set():
            await anyio.sleep(0)


@pytest.mark.anyio
async def test_cookie_tenants_stay_isolated_across_concurrent_sync_workers(monkeypatch):
    tenants = ("tenant_alpha", "tenant_beta")
    entered = threading.Barrier(2)
    sampled = threading.Barrier(2)
    loop_thread = threading.get_ident()
    validations = []
    results = {}

    monkeypatch.setattr(
        dependencies,
        "ensure_tenant_allowed_for_app",
        lambda tenant: {"tenant": tenant, "estado": "activo"},
    )

    def fake_validate_user(user_id, role):
        validations.append((user_id, role, tenant_schema_var.get()))

    monkeypatch.setattr(dependencies, "_validar_usuario_en_bd", fake_validate_user)

    def observe_worker():
        observation = {
            "thread": threading.get_ident(),
            "on_entry": tenant_schema_var.get(),
        }
        entered.wait(timeout=3)
        observation["during_overlap"] = tenant_schema_var.get()
        sampled.wait(timeout=3)
        observation["on_exit"] = tenant_schema_var.get()
        return observation

    async def run_request(tenant):
        token = create_access_token({"sub": "9", "rol": "admin", "tenant": tenant})
        request = CookieRequest(token)
        before_middleware = tenant_schema_var.get()

        async def call_next(request):
            downstream_entry = tenant_schema_var.get()
            user = await dependencies.get_current_user(request, token=None)
            after_auth = tenant_schema_var.get()
            inside_worker = await run_in_threadpool(observe_worker)
            after_worker = tenant_schema_var.get()
            return {
                "downstream_entry": downstream_entry,
                "user": user,
                "after_auth": after_auth,
                "inside_worker": inside_worker,
                "after_worker": after_worker,
            }

        downstream = await app_main.tenant_middleware(request, call_next)
        results[tenant] = {
            "before_middleware": before_middleware,
            "downstream": downstream,
            "after_middleware": tenant_schema_var.get(),
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
            entered.abort()
            sampled.abort()
    finally:
        tenant_schema_var.reset(outer_token)

    assert restored_outer == "tenant_outer"
    assert tenant_schema_var.get() == original
    assert sorted(validations) == [
        (9, "admin", "tenant_alpha"),
        (9, "admin", "tenant_beta"),
    ]
    assert len({
        result["downstream"]["inside_worker"]["thread"]
        for result in results.values()
    }) == 2

    for tenant, result in results.items():
        downstream = result["downstream"]
        assert result["before_middleware"] == "tenant_outer"
        assert result["after_middleware"] == "tenant_outer"
        assert downstream["downstream_entry"] is None
        assert downstream["user"] == {"id": 9, "rol": "admin", "tenant": tenant}
        assert downstream["after_auth"] == tenant
        assert downstream["after_worker"] == tenant
        assert downstream["inside_worker"] == {
            "thread": downstream["inside_worker"]["thread"],
            "on_entry": tenant,
            "during_overlap": tenant,
            "on_exit": tenant,
        }
        assert downstream["inside_worker"]["thread"] != loop_thread


@pytest.mark.anyio
async def test_raw_executor_control_does_not_copy_or_return_context_mutations():
    original = tenant_schema_var.get()
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_running_loop()

    def mutate_worker_context():
        before = tenant_schema_var.get()
        worker_token = tenant_schema_var.set("tenant_worker")
        try:
            return before, tenant_schema_var.get()
        finally:
            tenant_schema_var.reset(worker_token)

    try:
        await loop.run_in_executor(executor, tenant_schema_var.set, None)
        caller_token = tenant_schema_var.set("tenant_caller")
        try:
            worker_before, worker_during = await loop.run_in_executor(
                executor,
                mutate_worker_context,
            )
            caller_after = tenant_schema_var.get()
        finally:
            tenant_schema_var.reset(caller_token)
    finally:
        executor.shutdown(wait=True)

    assert worker_before is None
    assert worker_during == "tenant_worker"
    assert caller_after == "tenant_caller"
    assert tenant_schema_var.get() == original


@pytest.mark.anyio
async def test_threadpool_cancellation_waits_for_worker_cleanup():
    worker_started = threading.Event()
    allow_worker_to_finish = threading.Event()
    worker_finished = threading.Event()
    caller_finished = anyio.Event()
    cancellation_delivered = anyio.Event()

    def blocking_work():
        worker_started.set()
        try:
            if not allow_worker_to_finish.wait(timeout=3):
                raise TimeoutError("worker test timed out")
        finally:
            worker_finished.set()

    async def call_worker():
        try:
            await run_in_threadpool(blocking_work)
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
                inner_group.start_soon(call_worker)
                inner_group.start_soon(cancellation_sentinel)

    async with anyio.create_task_group() as task_group:
        cancel_scope = await task_group.start(run_cancelled_group)
        await _wait_for_thread_event(worker_started)

        cancel_scope.cancel()
        with anyio.fail_after(3):
            await cancellation_delivered.wait()

        assert not worker_finished.is_set()
        assert not caller_finished.is_set()
        allow_worker_to_finish.set()

    assert worker_finished.is_set()
    assert caller_finished.is_set()
