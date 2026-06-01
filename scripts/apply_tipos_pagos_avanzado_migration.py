"""Aplica la migración 20260517_tipos_pagos_avanzado a todos los tenants.

Uso:
    python scripts/apply_tipos_pagos_avanzado_migration.py
"""
import os
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


MIGRATION_FILE = (
    Path(__file__).resolve().parent.parent
    / "migrations"
    / "20260517_tipos_pagos_avanzado.sql"
)


def fetch_tenants(cursor):
    cursor.execute(
        """
        SELECT esquema_db
        FROM public.colegios
        WHERE LOWER(estado) IN ('activo', 'en_mora')
        ORDER BY esquema_db
        """
    )
    return [row[0] for row in cursor.fetchall()]


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


def apply_migration(cursor, schema, sql_script):
    cursor.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(schema)))
    cursor.execute(sql_script)


def main():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    database_url = os.getenv("DATABASE_URL")
    template_schema = os.getenv("DEFAULT_TENANT_SCHEMA", "tenant_colegio_1")

    if not database_url:
        raise RuntimeError("DATABASE_URL no está configurado")

    if not MIGRATION_FILE.exists():
        raise FileNotFoundError(f"No se encontró {MIGRATION_FILE}")

    sql_script = MIGRATION_FILE.read_text(encoding="utf-8")

    conn = psycopg2.connect(database_url)
    try:
        conn.autocommit = False
        cursor = conn.cursor()
        tenants = fetch_tenants(cursor)
        if template_schema not in tenants:
            tenants.insert(0, template_schema)

        for schema in tenants:
            if not table_exists(cursor, schema, "tipos_de_pagos"):
                print(f"{schema}.tipos_de_pagos: tabla no existe, omitida")
                continue

            apply_migration(cursor, schema, sql_script)
            print(f"{schema}: migración tipos_pagos_avanzado aplicada")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
