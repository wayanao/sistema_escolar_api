"""Reporta que migraciones le falta a cada tenant, sin modificar nada.

Uso:
    python scripts/auditar_migraciones_tenants.py

Compara los archivos de migrations/ contra public.schema_migrations e incluye a
TODOS los tenants registrados, tambien los suspendidos y cancelados que el
runner omite: son los que quedarian incompletos si alguien los reactiva.

Es un informe, no una correccion. Abre la transaccion como READ ONLY, no crea
public.schema_migrations si falta y termina con rollback. Sale con codigo 2 si
algun destino tiene migraciones pendientes o registradas con un checksum
distinto al del archivo actual.
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]

# El checksum se importa del runner en vez de reescribirlo: esta auditoria
# compara contra lo que apply_migration.py registro, asi que ambas partes deben
# usar exactamente la misma funcion. Una copia podria divergir en silencio.
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apply_migration import calculate_checksum  # noqa: E402


ESTADOS_QUE_EL_RUNNER_OMITE = {"suspendido", "cancelado"}


def cargar_migraciones(directorio: Path) -> dict[str, str]:
    """Nombre -> checksum de los .sql directos del directorio, sin recursion."""
    if not directorio.is_dir():
        return {}
    return {
        ruta.name: calculate_checksum(ruta.read_text(encoding="utf-8"))
        for ruta in sorted(directorio.glob("*.sql"))
    }


def fetch_tenants(cursor):
    """Todos los colegios registrados, sin filtrar por estado."""
    cursor.execute(
        """
        SELECT esquema_db, nombre, estado
        FROM public.colegios
        ORDER BY id
        """
    )
    return cursor.fetchall()


def historial_existe(cursor) -> bool:
    cursor.execute("SELECT to_regclass('public.schema_migrations')")
    row = cursor.fetchone()
    return bool(row and row[0])


def fetch_aplicadas(cursor):
    cursor.execute(
        """
        SELECT migration_name, target_schema, checksum
        FROM public.schema_migrations
        """
    )
    return cursor.fetchall()


def agrupar_por_schema(filas) -> dict[str, dict[str, str]]:
    aplicadas: dict[str, dict[str, str]] = {}
    for migration_name, target_schema, checksum in filas:
        aplicadas.setdefault(target_schema, {})[migration_name] = checksum
    return aplicadas


def revisar_destino(esperadas: dict[str, str], aplicadas: dict[str, str]):
    """Devuelve (faltantes, divergentes) conservando el orden de los archivos."""
    faltantes = [nombre for nombre in esperadas if nombre not in aplicadas]
    divergentes = [
        nombre
        for nombre, checksum in esperadas.items()
        if nombre in aplicadas and aplicadas[nombre] != checksum
    ]
    return faltantes, divergentes


def construir_informe(esperadas_tenant, esperadas_public, tenants, aplicadas):
    faltantes, divergentes = revisar_destino(esperadas_public, aplicadas.get("public", {}))
    informe = [
        {
            "schema": "public",
            "nombre": "Schema publico",
            "estado": "publico",
            "omitido_por_el_runner": False,
            "faltantes": faltantes,
            "divergentes": divergentes,
        }
    ]

    for esquema_db, nombre, estado in tenants:
        estado_normalizado = str(estado or "").strip().lower()
        faltantes, divergentes = revisar_destino(
            esperadas_tenant, aplicadas.get(esquema_db, {})
        )
        informe.append(
            {
                "schema": esquema_db,
                "nombre": nombre,
                "estado": estado_normalizado,
                "omitido_por_el_runner": estado_normalizado in ESTADOS_QUE_EL_RUNNER_OMITE,
                "faltantes": faltantes,
                "divergentes": divergentes,
            }
        )
    return informe


def destinos_con_pendientes(informe):
    return [
        entrada for entrada in informe if entrada["faltantes"] or entrada["divergentes"]
    ]


def omitidos_y_atrasados(informe):
    """Los que el runner nunca alcanza y ademas estan atrasados."""
    return [
        entrada
        for entrada in destinos_con_pendientes(informe)
        if entrada["omitido_por_el_runner"]
    ]


def formatear_informe(informe):
    lineas = []
    for entrada in informe:
        marca = " [el runner lo omite]" if entrada["omitido_por_el_runner"] else ""
        cabecera = f"{entrada['schema']} ({entrada['nombre']}, {entrada['estado']}){marca}"

        if not entrada["faltantes"] and not entrada["divergentes"]:
            lineas.append(f"OK        {cabecera}")
            continue

        lineas.append(
            f"PENDIENTE {cabecera}: "
            f"faltan {len(entrada['faltantes'])}, divergen {len(entrada['divergentes'])}"
        )
        for nombre in entrada["faltantes"]:
            lineas.append(f"            falta      {nombre}")
        for nombre in entrada["divergentes"]:
            lineas.append(f"            divergente {nombre}")
    return lineas


def main():
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("X DATABASE_URL no esta definido en .env")
        return 1

    esperadas_tenant = cargar_migraciones(ROOT_DIR / "migrations")
    esperadas_public = cargar_migraciones(ROOT_DIR / "migrations" / "public")

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        cursor.execute("SET TRANSACTION READ ONLY")

        if not historial_existe(cursor):
            print("X public.schema_migrations no existe: ninguna migracion fue registrada.")
            return 2

        tenants = fetch_tenants(cursor)
        aplicadas = agrupar_por_schema(fetch_aplicadas(cursor))
        informe = construir_informe(
            esperadas_tenant, esperadas_public, tenants, aplicadas
        )

        print(
            f"Revisando {len(esperadas_tenant)} migracion(es) de tenant y "
            f"{len(esperadas_public)} publica(s) en {len(informe)} destino(s)..."
        )
        for linea in formatear_informe(informe):
            print(linea)

        reactivables = omitidos_y_atrasados(informe)
        if reactivables:
            print(
                f"! {len(reactivables)} destino(s) que el runner omite estan atrasados "
                "y quedarian incompletos si se reactivan."
            )

        pendientes = destinos_con_pendientes(informe)
        if pendientes:
            print(f"Auditoria finalizada con {len(pendientes)} destino(s) pendiente(s).")
            return 2

        print("Auditoria finalizada: todos los destinos al dia.")
        return 0
    finally:
        conn.rollback()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
