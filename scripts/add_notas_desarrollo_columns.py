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


def add_columns(cursor, schema):
    cursor.execute(
        sql.SQL("""
            ALTER TABLE {}.notas_detalle
            ADD COLUMN IF NOT EXISTS tipo_evaluacion VARCHAR(30) DEFAULT 'numerica',
            ADD COLUMN IF NOT EXISTS valoracion VARCHAR(30)
        """).format(sql.Identifier(schema))
    )


def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no esta configurado")

    conn = psycopg2.connect(database_url)
    try:
        conn.autocommit = False
        cursor = conn.cursor()
        tenants = fetch_tenants(cursor)

        for schema in tenants:
            if table_exists(cursor, schema, "notas_detalle"):
                add_columns(cursor, schema)
                print(f"{schema}.notas_detalle: columnas verificadas")
            else:
                print(f"{schema}.notas_detalle: tabla no existe, omitida")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
