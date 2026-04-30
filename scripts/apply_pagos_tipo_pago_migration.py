import os

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


load_dotenv()


def fetch_tenants(cursor):
    cursor.execute("""
        SELECT esquema_db
        FROM public.colegios
        WHERE estado = 'activo'
        ORDER BY esquema_db
    """)
    return [row[0] for row in cursor.fetchall()]


def table_exists(cursor, schema, table):
    cursor.execute("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
    """, (schema, table))
    return cursor.fetchone() is not None


def apply_migration(cursor, schema):
    cursor.execute(
        sql.SQL("""
            ALTER TABLE {}.pagos
            ALTER COLUMN tipo_pago TYPE VARCHAR(100)
        """).format(sql.Identifier(schema))
    )


def main():
    database_url = os.getenv("DATABASE_URL")
    template_schema = os.getenv("DEFAULT_TENANT_SCHEMA", "tenant_colegio_1")

    if not database_url:
        raise RuntimeError("DATABASE_URL no esta configurado")

    conn = psycopg2.connect(database_url)
    try:
        conn.autocommit = False
        cursor = conn.cursor()
        tenants = fetch_tenants(cursor)
        if template_schema not in tenants:
            tenants.insert(0, template_schema)

        for schema in tenants:
            if not table_exists(cursor, schema, "pagos"):
                print(f"{schema}.pagos: tabla no existe, omitida")
                continue
            apply_migration(cursor, schema)
            print(f"{schema}.pagos.tipo_pago: longitud verificada")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
