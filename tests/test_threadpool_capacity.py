import threading

import anyio
import psycopg2
import pytest
from psycopg2 import extensions
from psycopg2.pool import PoolError, ThreadedConnectionPool
from starlette.concurrency import run_in_threadpool

from app import main as app_main
from app.config import settings
from app.controllers import tipos_pagos_controller


@pytest.fixture
def anyio_backend():
    return "asyncio"


class _ConnectionInfo:
    def __init__(self):
        self.transaction_status = extensions.TRANSACTION_STATUS_IDLE


class _PooledConnection:
    def __init__(self):
        self.closed = 0
        self.info = _ConnectionInfo()

    def rollback(self):
        pass

    def close(self):
        self.closed = 1


def _build_real_pool(monkeypatch, max_connections):
    monkeypatch.setattr(
        psycopg2,
        "connect",
        lambda *_args, **_kwargs: _PooledConnection(),
    )
    return ThreadedConnectionPool(
        minconn=1,
        maxconn=max_connections,
        dsn="dsn-falso",
    )


class _LeaseTracker:
    def __init__(self, pool):
        self.pool = pool
        self.lock = threading.Lock()
        self.active = 0
        self.peak = 0
        self.per_thread = {}
        self.per_thread_peak = {}

    def checkout(self):
        connection = self.pool.getconn()
        thread_id = threading.get_ident()
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.per_thread[thread_id] = self.per_thread.get(thread_id, 0) + 1
            self.per_thread_peak[thread_id] = max(
                self.per_thread_peak.get(thread_id, 0),
                self.per_thread[thread_id],
            )
        return connection

    def checkin(self, connection):
        thread_id = threading.get_ident()
        self.pool.putconn(connection)
        with self.lock:
            self.active -= 1
            self.per_thread[thread_id] -= 1


@pytest.mark.parametrize(
    ("max_connections", "expected_tokens"),
    [(2, 1), (9, 4), (10, 5), (12, 6)],
)
@pytest.mark.anyio
async def test_threadpool_capacity_formula_uses_two_connections_per_worker(
    monkeypatch,
    max_connections,
    expected_tokens,
):
    limiter = anyio.to_thread.current_default_thread_limiter()
    original_tokens = limiter.total_tokens
    monkeypatch.setattr(settings, "DB_POOL_MAX_CONNECTIONS", max_connections)
    monkeypatch.setattr(app_main, "close_pool", lambda: None)

    try:
        limiter.total_tokens = 40
        async with app_main.lifespan(app_main.app):
            assert limiter.total_tokens == expected_tokens
    finally:
        limiter.total_tokens = original_tokens


@pytest.mark.anyio
async def test_threadpool_capacity_formula_rejects_an_unsafe_pool_size(monkeypatch):
    limiter = anyio.to_thread.current_default_thread_limiter()
    original_tokens = limiter.total_tokens
    monkeypatch.setattr(settings, "DB_POOL_MAX_CONNECTIONS", 1)
    monkeypatch.setattr(app_main, "close_pool", lambda: pytest.fail("no debe cerrar"))

    try:
        with pytest.raises(RuntimeError, match="at least 2"):
            async with app_main.lifespan(app_main.app):
                pytest.fail("el lifespan no debe arrancar")
    finally:
        limiter.total_tokens = original_tokens


@pytest.mark.anyio
async def test_threadpool_capacity_is_set_before_lifespan_yield(monkeypatch):
    limiter = anyio.to_thread.current_default_thread_limiter()
    original_tokens = limiter.total_tokens
    closes = []
    monkeypatch.setattr(settings, "DB_POOL_MAX_CONNECTIONS", 12)
    monkeypatch.setattr(app_main, "close_pool", lambda: closes.append("closed"))

    try:
        limiter.total_tokens = 40
        async with app_main.lifespan(app_main.app):
            assert limiter.total_tokens == 6
            assert closes == []
        assert closes == ["closed"]
    finally:
        limiter.total_tokens = original_tokens


@pytest.mark.anyio
async def test_shared_limiter_also_bounds_non_database_worker_work(monkeypatch):
    max_connections = 10
    expected_tokens = (
        max_connections // app_main.MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER
    )
    limiter = anyio.to_thread.current_default_thread_limiter()
    original_tokens = limiter.total_tokens
    gate = threading.Barrier(expected_tokens)
    lock = threading.Lock()
    active = 0
    peak = 0
    completed = []

    def generic_worker(worker_id):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        try:
            gate.wait(timeout=3)
            completed.append(worker_id)
        finally:
            with lock:
                active -= 1

    monkeypatch.setattr(
        settings,
        "DB_POOL_MAX_CONNECTIONS",
        max_connections,
    )
    monkeypatch.setattr(app_main, "close_pool", lambda: None)

    try:
        limiter.total_tokens = 40
        async with app_main.lifespan(app_main.app):
            with anyio.fail_after(5):
                async with anyio.create_task_group() as task_group:
                    for worker_id in range(expected_tokens * 2):
                        task_group.start_soon(
                            run_in_threadpool,
                            generic_worker,
                            worker_id,
                        )
    finally:
        limiter.total_tokens = original_tokens

    assert sorted(completed) == list(range(expected_tokens * 2))
    assert peak == expected_tokens
    assert active == 0


@pytest.mark.anyio
async def test_threadpool_capacity_prevents_exhaustion_with_two_leases_per_worker(
    monkeypatch,
):
    max_connections = 10
    tokens = max_connections // app_main.MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER
    pool = _build_real_pool(monkeypatch, max_connections)
    tracker = _LeaseTracker(pool)
    first_checkout = threading.Barrier(tokens)
    second_checkout = threading.Barrier(tokens)
    completed = []
    limiter = anyio.to_thread.current_default_thread_limiter()
    original_tokens = limiter.total_tokens

    def worker(worker_id):
        first = tracker.checkout()
        try:
            first_checkout.wait(timeout=3)
            second = tracker.checkout()
            try:
                second_checkout.wait(timeout=3)
                completed.append(worker_id)
            finally:
                tracker.checkin(second)
        finally:
            tracker.checkin(first)

    try:
        limiter.total_tokens = tokens
        with anyio.fail_after(5):
            async with anyio.create_task_group() as task_group:
                for worker_id in range(tokens * 2):
                    task_group.start_soon(run_in_threadpool, worker, worker_id)
    finally:
        limiter.total_tokens = original_tokens
        pool.closeall()

    assert sorted(completed) == list(range(tokens * 2))
    assert tracker.peak == max_connections
    assert max(tracker.per_thread_peak.values()) == 2
    assert tracker.active == 0


@pytest.mark.anyio
async def test_one_extra_threadpool_token_reproduces_pool_exhaustion(monkeypatch):
    max_connections = 10
    tokens = (
        max_connections // app_main.MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER
    ) + 1
    pool = _build_real_pool(monkeypatch, max_connections)
    tracker = _LeaseTracker(pool)
    first_checkout = threading.Barrier(tokens)
    all_attempted_second = threading.Barrier(tokens)
    pool_errors = []
    limiter = anyio.to_thread.current_default_thread_limiter()
    original_tokens = limiter.total_tokens

    def worker(worker_id):
        first = tracker.checkout()
        second = None
        try:
            first_checkout.wait(timeout=3)
            try:
                second = tracker.checkout()
            except PoolError:
                pool_errors.append(worker_id)
            finally:
                all_attempted_second.wait(timeout=3)
            if second is not None:
                tracker.checkin(second)
        finally:
            tracker.checkin(first)

    try:
        limiter.total_tokens = tokens
        with anyio.fail_after(5):
            async with anyio.create_task_group() as task_group:
                for worker_id in range(tokens):
                    task_group.start_soon(run_in_threadpool, worker, worker_id)
    finally:
        limiter.total_tokens = original_tokens
        pool.closeall()

    assert len(pool_errors) == 2
    assert tracker.peak == max_connections
    assert tracker.active == 0


class _ControllerCursor:
    def __init__(self):
        self.query = ""

    def execute(self, query, _params=None):
        self.query = query

    def fetchone(self):
        if "SELECT al.anio, al.estado" in self.query:
            # Año lectivo, paso 3.7: la guardia de escritura ve 2026 activo.
            return (2026, "activo")
        if "AS cursos_de_otro_anio" in self.query:
            # El concepto existe y ningun curso es de otro año (fase 3 del año
            # lectivo, paso 3.3).
            return {"cursos_de_otro_anio": []}
        if "SELECT curso_id FROM estudiantes" in self.query:
            # Los upsert usan RealDictCursor desde que dejaron de anidar
            # conexiones, asi que leen la columna por nombre.
            return {"curso_id": 3}
        return (1,)

    def fetchall(self):
        if "information_schema.tables" in self.query:
            return [
                ("tipos_pagos_cursos",),
                ("tipos_pagos_estudiantes",),
            ]
        return []

    def close(self):
        pass


class _ControllerConnection:
    def __init__(self, tracker):
        self.tracker = tracker
        self.closed = False

    def cursor(self, **_kwargs):
        return _ControllerCursor()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        if not self.closed:
            self.closed = True
            self.tracker.release()


class _ControllerConnectionTracker:
    def __init__(self):
        self.active = 0
        self.peak = 0

    def acquire(self):
        self.active += 1
        self.peak = max(self.peak, self.active)
        return _ControllerConnection(self)

    def release(self):
        self.active -= 1


@pytest.mark.parametrize(
    "call_controller",
    [
        pytest.param(
            lambda: tipos_pagos_controller.upsert_cursos_asignados(7, []),
            id="cursos-asignados",
        ),
        pytest.param(
            lambda: tipos_pagos_controller.upsert_valor_personalizado_estudiante(
                11,
                7,
                25000,
            ),
            id="valor-personalizado",
        ),
    ],
)
def test_registered_upsert_paths_no_longer_nest_connections(monkeypatch, call_controller):
    """Estos dos caminos sostenian dos conexiones a la vez y ya no.

    Releian su estado despues del `commit` llamando a una funcion que abria su
    propia conexion, y el `return` se evaluaba antes del `finally`, asi que las
    dos se solapaban. Desde 2026-08-17 releen con el mismo cursor antes de
    confirmar.

    Eran los dos unicos ejemplos registrados que justificaban
    `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2`. La constante **no se toca**:
    sigue como margen de seguridad y su revision pertenece a una auditoria de la
    capa 2, no a esta correccion.
    """
    tracker = _ControllerConnectionTracker()
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", tracker.acquire)

    result = call_controller()

    assert result == []
    assert tracker.peak == 1
    assert tracker.active == 0
