"""Audita integridad de plan_de_clases sin modificar la base de datos.

Uso:
    python scripts/auditar_plan_de_clases_integridad.py

Revisa todos los tenants registrados y el schema plantilla configurado. Sale
con codigo 2 si encuentra filas sin asignacion/fecha o grupos duplicados.
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql


ROOT_DIR = Path(__file__).resolve().parents[1]


def fetch_tenants(cursor):
    cursor.execute(
        """
        SELECT esquema_db, nombre, estado
        FROM public.colegios
        ORDER BY id
        """
    )
    return cursor.fetchall()


def table_exists(cursor, schema):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = 'plan_de_clases'
        """,
        (schema,),
    )
    return cursor.fetchone() is not None


def audit_schema(cursor, schema):
    cursor.execute(
        sql.SQL(
            """
            SELECT COUNT(*)
            FROM {}.plan_de_clases
            WHERE asignacion_id IS NULL OR fecha IS NULL
            """
        ).format(sql.Identifier(schema))
    )
    invalidos = cursor.fetchone()[0]

    cursor.execute(
        sql.SQL(
            """
            SELECT COUNT(*)
            FROM (
                SELECT asignacion_id, fecha
                FROM {}.plan_de_clases
                GROUP BY asignacion_id, fecha
                HAVING COUNT(*) > 1
            ) duplicados
            """
        ).format(sql.Identifier(schema))
    )
    grupos_duplicados = cursor.fetchone()[0]

    return {
        "invalidos": invalidos,
        "grupos_duplicados": grupos_duplicados,
    }


def main():
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    template_schema = os.getenv("DEFAULT_TENANT_SCHEMA", "tenant_colegio_1")

    if not database_url:
        print("X DATABASE_URL no esta definido en .env")
        return 1

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        cursor.execute("SET TRANSACTION READ ONLY")
        tenants = fetch_tenants(cursor)
        schemas = [(schema, nombre, estado) for schema, nombre, estado in tenants]

        if template_schema and all(schema != template_schema for schema, _, _ in schemas):
            schemas.insert(0, (template_schema, "Schema plantilla", "plantilla"))

        problemas = 0
        print(f"Auditando plan_de_clases en {len(schemas)} schema(s)...")

        for schema, nombre, estado in schemas:
            if not table_exists(cursor, schema):
                print(f"OMITIDO {schema} ({nombre}, {estado}): tabla no existe")
                continue

            resultado = audit_schema(cursor, schema)
            invalidos = resultado["invalidos"]
            duplicados = resultado["grupos_duplicados"]

            if invalidos or duplicados:
                problemas += 1
                print(
                    f"REVISAR {schema} ({nombre}, {estado}): "
                    f"invalidos={invalidos}, grupos_duplicados={duplicados}"
                )
            else:
                print(f"OK {schema} ({nombre}, {estado})")

        if problemas:
            print(f"Auditoria finalizada con problemas en {problemas} schema(s).")
            return 2

        print("Auditoria finalizada sin inconsistencias.")
        return 0
    finally:
        conn.rollback()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
