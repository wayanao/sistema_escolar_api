"""Verifica el esquema de revision del plan de clases sin modificar datos."""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql


ROOT_DIR = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = {
    "estado_revision",
    "version_revision",
    "enviado_at",
    "admin_visto_at",
    "admin_visto_por",
    "revisado_at",
    "revisado_por",
}


def fetch_tenants(cursor):
    cursor.execute(
        """
        SELECT esquema_db, nombre, estado
        FROM public.colegios
        WHERE LOWER(estado) IN ('activo', 'en_mora')
        ORDER BY id
        """
    )
    return cursor.fetchall()


def fetch_columns(cursor, schema):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = 'plan_de_clases'
        """,
        (schema,),
    )
    return {row[0] for row in cursor.fetchall()}


def table_exists(cursor, schema, table):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        (schema, table),
    )
    return cursor.fetchone() is not None


def audit_schema(cursor, schema):
    columns = fetch_columns(cursor, schema)
    missing_columns = sorted(REQUIRED_COLUMNS - columns)
    observations_table = table_exists(
        cursor,
        schema,
        "plan_de_clases_observaciones",
    )
    admin_notifications_table = table_exists(
        cursor,
        schema,
        "plan_de_clases_notificaciones_admin",
    )

    invalid_plans = None
    if not missing_columns:
        cursor.execute(
            sql.SQL(
                """
                SELECT COUNT(*)
                FROM {}.plan_de_clases
                WHERE estado_revision NOT IN (
                    'pendiente', 'visto', 'con_observaciones', 'revisado'
                )
                   OR version_revision < 1
                   OR enviado_at IS NULL
                """
            ).format(sql.Identifier(schema))
        )
        invalid_plans = cursor.fetchone()[0]

    return {
        "missing_columns": missing_columns,
        "observations_table": observations_table,
        "admin_notifications_table": admin_notifications_table,
        "invalid_plans": invalid_plans,
    }


def main():
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("X DATABASE_URL no esta definido en .env")
        return 1

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        cursor.execute("SET TRANSACTION READ ONLY")
        tenants = fetch_tenants(cursor)
        problemas = 0
        print(f"Verificando revision de planes en {len(tenants)} schema(s)...")

        for schema, nombre, estado in tenants:
            result = audit_schema(cursor, schema)
            if (
                result["missing_columns"]
                or not result["observations_table"]
                or not result["admin_notifications_table"]
                or result["invalid_plans"] != 0
            ):
                problemas += 1
                print(
                    f"REVISAR {schema} ({nombre}, {estado}): "
                    f"columnas_faltantes={result['missing_columns']}, "
                    f"tabla_observaciones={result['observations_table']}, "
                    f"tabla_notificaciones={result['admin_notifications_table']}, "
                    f"planes_invalidos={result['invalid_plans']}"
                )
            else:
                print(f"OK {schema} ({nombre}, {estado})")

        if problemas:
            print(f"Verificacion finalizada con problemas en {problemas} schema(s).")
            return 2

        print("Verificacion finalizada sin inconsistencias.")
        return 0
    finally:
        conn.rollback()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
