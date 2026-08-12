r"""Mide la frontera de concurrencia de ``get_current_user`` sin usar DB ni red.

El arnes conserva la funcion real de autenticacion y sustituye solamente sus
dos operaciones DB por dobles hermeticos. Dos tareas con tenants distintos se
inician juntas; cada validacion bloquea durante una demora conocida mientras un
heartbeat intenta despertar en el event loop.

El mismo comando sirve antes y despues del offload de autenticacion. No usa los
tiempos como una compuerta funcional: informa ubicacion de hilos, solapamiento y
contextos para que ambos estados puedan compararse con el mismo procedimiento.

Uso:

    .\venv\Scripts\python.exe scripts\measure_auth_concurrency.py
    .\venv\Scripts\python.exe scripts\measure_auth_concurrency.py --json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import threading
import time
from pathlib import Path

import anyio

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import dependencies  # noqa: E402
from app.globals import tenant_schema_var  # noqa: E402
from app.security import create_access_token  # noqa: E402


TENANTS = ("tenant_alpha", "tenant_beta")
OUTER_TENANT = "tenant_measurement_outer"


class CookieRequest:
    def __init__(self, token: str):
        self.cookies = {"token": token}


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("debe ser mayor que cero")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("debe ser mayor que cero")
    return parsed


def _thread_location(thread_ids: list[int], loop_thread_id: int) -> str:
    if all(thread_id == loop_thread_id for thread_id in thread_ids):
        return "event_loop"
    if all(thread_id != loop_thread_id for thread_id in thread_ids):
        return "worker"
    return "mixed"


async def _measure_once(
    run_number: int,
    validation_seconds: float,
    heartbeat_seconds: float,
) -> dict:
    lock = threading.Lock()
    active_validations = 0
    max_overlap = 0
    ensure_observations: list[dict] = []
    validation_observations: list[dict] = []
    results: dict[str, dict] = {}
    caller_contexts: dict[str, str | None] = {}
    heartbeat_elapsed_ms: float | None = None
    loop_thread_id = threading.get_ident()

    def fake_ensure_tenant(tenant: str) -> dict:
        observation = {
            "tenant": tenant,
            "context": tenant_schema_var.get(),
            "thread_id": threading.get_ident(),
        }
        with lock:
            ensure_observations.append(observation)
        return {"tenant": tenant, "estado": "activo"}

    def fake_validate_user(user_id: int, role: str) -> None:
        nonlocal active_validations, max_overlap
        observation = {
            "user_id": user_id,
            "role": role,
            "context": tenant_schema_var.get(),
            "thread_id": threading.get_ident(),
        }
        with lock:
            active_validations += 1
            max_overlap = max(max_overlap, active_validations)
            validation_observations.append(observation)
        try:
            time.sleep(validation_seconds)
        finally:
            with lock:
                active_validations -= 1

    dependencies.ensure_tenant_allowed_for_app = fake_ensure_tenant
    dependencies._validar_usuario_en_bd = fake_validate_user
    started_at = time.perf_counter()

    async def authenticate(tenant: str) -> None:
        request_token = tenant_schema_var.set(None)
        token = create_access_token(
            {"sub": "9", "rol": "admin", "tenant": tenant}
        )
        try:
            results[tenant] = await dependencies.get_current_user(
                CookieRequest(token),
                token=None,
            )
            caller_contexts[tenant] = tenant_schema_var.get()
        finally:
            tenant_schema_var.reset(request_token)

    async def heartbeat() -> None:
        nonlocal heartbeat_elapsed_ms
        await anyio.sleep(heartbeat_seconds)
        heartbeat_elapsed_ms = (time.perf_counter() - started_at) * 1000

    async with anyio.create_task_group() as task_group:
        for tenant in TENANTS:
            task_group.start_soon(authenticate, tenant)
        task_group.start_soon(heartbeat)

    total_ms = (time.perf_counter() - started_at) * 1000
    expected_results = {
        tenant: {"id": 9, "rol": "admin", "tenant": tenant}
        for tenant in TENANTS
    }
    ensure_observations.sort(key=lambda item: item["tenant"])
    validation_observations.sort(key=lambda item: str(item["context"]))

    if results != expected_results:
        raise RuntimeError(f"Resultados de autenticacion inesperados: {results!r}")
    if caller_contexts != {tenant: tenant for tenant in TENANTS}:
        raise RuntimeError(f"Contexto incorrecto al volver al llamador: {caller_contexts!r}")
    if [item["tenant"] for item in ensure_observations] != sorted(TENANTS):
        raise RuntimeError(f"Tenants inesperados en ensure: {ensure_observations!r}")
    if sorted(item["context"] for item in validation_observations) != sorted(TENANTS):
        raise RuntimeError(
            f"Perdida o mezcla de tenant durante validacion: {validation_observations!r}"
        )
    if any(
        item["user_id"] != 9 or item["role"] != "admin"
        for item in validation_observations
    ):
        raise RuntimeError(
            f"Argumentos de validacion inesperados: {validation_observations!r}"
        )
    if heartbeat_elapsed_ms is None:
        raise RuntimeError("El heartbeat no llego a ejecutarse")
    if tenant_schema_var.get() != OUTER_TENANT:
        raise RuntimeError("El contexto exterior no fue restaurado")

    ensure_thread_ids = [item["thread_id"] for item in ensure_observations]
    validation_thread_ids = [
        item["thread_id"] for item in validation_observations
    ]
    return {
        "run": run_number,
        "total_ms": round(total_ms, 3),
        "heartbeat_elapsed_ms": round(heartbeat_elapsed_ms, 3),
        "heartbeat_delay_ms": round(
            heartbeat_elapsed_ms - heartbeat_seconds * 1000,
            3,
        ),
        "max_validation_overlap": max_overlap,
        "event_loop_thread_id": loop_thread_id,
        "ensure_location": _thread_location(ensure_thread_ids, loop_thread_id),
        "validation_location": _thread_location(
            validation_thread_ids,
            loop_thread_id,
        ),
        "ensure_thread_ids": ensure_thread_ids,
        "validation_thread_ids": validation_thread_ids,
        "ensure_observations": ensure_observations,
        "validation_observations": validation_observations,
        "caller_contexts": caller_contexts,
    }


async def measure(
    runs: int,
    validation_ms: float,
    heartbeat_ms: float,
) -> dict:
    original_ensure = dependencies.ensure_tenant_allowed_for_app
    original_validate = dependencies._validar_usuario_en_bd
    outer_token = tenant_schema_var.set(OUTER_TENANT)
    measurements: list[dict] = []
    try:
        for run_number in range(1, runs + 1):
            measurements.append(
                await _measure_once(
                    run_number,
                    validation_ms / 1000,
                    heartbeat_ms / 1000,
                )
            )
        outer_context_restored = tenant_schema_var.get() == OUTER_TENANT
    finally:
        dependencies.ensure_tenant_allowed_for_app = original_ensure
        dependencies._validar_usuario_en_bd = original_validate
        tenant_schema_var.reset(outer_token)

    return {
        "configuration": {
            "runs": runs,
            "tenants": list(TENANTS),
            "validation_ms": validation_ms,
            "heartbeat_ms": heartbeat_ms,
            "database": "fake",
            "network": False,
        },
        "summary": {
            "median_total_ms": round(
                statistics.median(item["total_ms"] for item in measurements),
                3,
            ),
            "median_heartbeat_delay_ms": round(
                statistics.median(
                    item["heartbeat_delay_ms"] for item in measurements
                ),
                3,
            ),
            "max_validation_overlap": max(
                item["max_validation_overlap"] for item in measurements
            ),
            "ensure_locations": sorted(
                {item["ensure_location"] for item in measurements}
            ),
            "validation_locations": sorted(
                {item["validation_location"] for item in measurements}
            ),
            "outer_context_restored": outer_context_restored,
            "functional_checks": "passed",
        },
        "runs": measurements,
    }


def _print_text(report: dict) -> None:
    config = report["configuration"]
    print("Medicion hermetica de autenticacion concurrente")
    print(
        f"Configuracion: {config['runs']} rondas, "
        f"validacion={config['validation_ms']:.1f} ms, "
        f"heartbeat={config['heartbeat_ms']:.1f} ms"
    )
    for item in report["runs"]:
        print(
            f"Ronda {item['run']}: total={item['total_ms']:.3f} ms, "
            f"retardo heartbeat={item['heartbeat_delay_ms']:.3f} ms, "
            f"solapamiento={item['max_validation_overlap']}, "
            f"ensure={item['ensure_location']}, "
            f"validacion={item['validation_location']}"
        )

    summary = report["summary"]
    print("Resumen:")
    print(f"  mediana total: {summary['median_total_ms']:.3f} ms")
    print(
        "  mediana retardo heartbeat: "
        f"{summary['median_heartbeat_delay_ms']:.3f} ms"
    )
    print(f"  solapamiento maximo: {summary['max_validation_overlap']}")
    print(f"  ubicacion ensure: {', '.join(summary['ensure_locations'])}")
    print(
        "  ubicacion validacion: "
        f"{', '.join(summary['validation_locations'])}"
    )
    print(f"  contexto exterior restaurado: {summary['outer_context_restored']}")
    print(f"  comprobaciones funcionales: {summary['functional_checks']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=_positive_int, default=5)
    parser.add_argument("--validation-ms", type=_positive_float, default=100.0)
    parser.add_argument("--heartbeat-ms", type=_positive_float, default=20.0)
    parser.add_argument(
        "--json",
        action="store_true",
        help="imprime el reporte completo como JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = anyio.run(
        measure,
        args.runs,
        args.validation_ms,
        args.heartbeat_ms,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
