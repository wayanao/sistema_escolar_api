import os

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


load_dotenv()

INDEXES = [
    ("estudiantes", "idx_estudiantes_curso_id", ["curso_id"]),
    ("pagos", "idx_pagos_estudiante_id", ["estudiante_id"]),
    ("asistencia", "idx_asistencia_estudiante_fecha", ["estudiante_id", "fecha"]),
    ("notas_detalle", "idx_notas_detalle_estudiante_asignacion", ["estudiante_id", "asignacion_id"]),
    ("boletin_cabecera", "idx_boletin_cabecera_lookup", ["estudiante_id", "asignacion_id", "periodo"]),
    ("asignaciones", "idx_asignaciones_curso_id", ["curso_id"]),
    ("asignaciones", "idx_asignaciones_profesor_id", ["profesor_id"]),
]


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


def create_index(cursor, schema, table, index_name, columns):
    index_identifier = f"{schema}_{index_name}"
    cursor.execute(
        sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {}.{} ({})").format(
            sql.Identifier(index_identifier),
            sql.Identifier(schema),
            sql.Identifier(table),
            sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        )
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
            for table, index_name, columns in INDEXES:
                if table_exists(cursor, schema, table):
                    create_index(cursor, schema, table, index_name, columns)
                    print(f"{schema}.{table}: indice {index_name} verificado")
                else:
                    print(f"{schema}.{table}: tabla no existe, omitida")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
