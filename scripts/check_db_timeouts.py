"""Comprueba contra la base real que los timeouts se aplican de verdad.

Existe porque una prueba hermetica no puede cubrir la diferencia entre un
endpoint agrupado y uno directo. El `-pooler` de Neon es PgBouncer en modo
transaccion y rechaza parametros de arranque que no sabe rastrear; un endpoint
directo los aceptaria. Solo una conexion real distingue los dos casos.

Uso:

    .\\venv\\Scripts\\python.exe scripts\\check_db_timeouts.py
    .\\venv\\Scripts\\python.exe scripts\\check_db_timeouts.py --forzar

Sin argumentos solo lee: abre una conexion, consulta los valores efectivos y la
devuelve al pool.

Con --forzar comprueba ademas que el timeout se CUMPLE, no solo que este
configurado. Baja statement_timeout a un segundo para esa transaccion y lanza un
pg_sleep mas largo; PostgreSQL debe cancelar la consulta. Usa un valor corto para
no esperar los 30 s reales, pero recorre exactamente el mismo camino.

En ningun caso escribe nada ni altera datos, y no imprime credenciales.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.db.session import build_timeout_statement, close_pool, get_connection  # noqa: E402
from app.globals import tenant_schema_var  # noqa: E402

AJUSTES = (
    "statement_timeout",
    "lock_timeout",
    "idle_in_transaction_session_timeout",
)


def describir_endpoint() -> str:
    host = urlparse(settings.DATABASE_URL).hostname or ""
    if not host:
        return "desconocido"
    tipo = "AGRUPADO (pooler)" if "-pooler" in host else "DIRECTO"
    # Se muestra solo el dominio, nunca el usuario ni la contrasena.
    return f"{tipo}  ·  ...{host[-40:]}"


def forzar_timeout(conexion) -> bool:
    """Comprueba que statement_timeout se cumple, no solo que este fijado.

    Devuelve True si PostgreSQL cancelo la consulta, que es el resultado
    esperado.
    """
    print("\nForzando un timeout deliberado...")
    cursor = conexion.cursor()
    inicio = time.monotonic()
    try:
        cursor.execute("SELECT set_config('statement_timeout', '1000', TRUE)")
        cursor.execute("SELECT pg_sleep(5)")
    except psycopg2.errors.QueryCanceled:
        transcurrido = time.monotonic() - inicio
        print(f"  Consulta cancelada tras {transcurrido:.2f} s, como se esperaba.")
        print("  El timeout se CUMPLE, no solo esta configurado.")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  Error inesperado: {type(exc).__name__}: {exc}")
        return False
    else:
        transcurrido = time.monotonic() - inicio
        print(f"  La consulta termino en {transcurrido:.2f} s SIN cancelarse.")
        print("  El timeout NO se esta aplicando. Revisar antes de confiar en el.")
        return False
    finally:
        cursor.close()


def main() -> int:
    forzar = "--forzar" in sys.argv
    print(f"Endpoint      : {describir_endpoint()}")
    print(f"connect_timeout configurado: {settings.DB_CONNECT_TIMEOUT_SECONDS} s")

    sentencia = build_timeout_statement()
    if sentencia is None:
        print("\nNo hay timeouts de sesion configurados: los tres estan en 0.")
    else:
        print(f"Sentencia por transaccion : {sentencia[0]}")

    tenant = settings.DEFAULT_TENANT_SCHEMA
    token = tenant_schema_var.set(tenant)
    print(f"Tenant usado  : {tenant}\n")

    try:
        conexion = get_connection()
    except Exception as exc:  # noqa: BLE001
        print("FALLO al abrir la conexion:")
        print(f"  {type(exc).__name__}: {exc}")
        print("\nSi el mensaje menciona 'unsupported startup parameter in options',")
        print("algun timeout volvio a enviarse en el paquete de arranque.")
        tenant_schema_var.reset(token)
        return 1

    cumplido = True
    try:
        cursor = conexion.cursor()
        try:
            for nombre in AJUSTES:
                cursor.execute(f"SHOW {nombre}")
                print(f"  {nombre:38s} = {cursor.fetchone()[0]}")
        finally:
            cursor.close()

        if forzar:
            cumplido = forzar_timeout(conexion)
    finally:
        conexion.close()
        close_pool()
        tenant_schema_var.reset(token)

    print("\nConexion abierta y timeouts aplicados correctamente.")
    print("Un valor en 0 significa que ese timeout no esta fijado.")
    if not forzar:
        print("Para comprobar ademas que se CUMPLEN, repetir con --forzar.")
    return 0 if cumplido else 1


if __name__ == "__main__":
    raise SystemExit(main())
