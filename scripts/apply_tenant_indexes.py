import argparse
import os

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


load_dotenv()

INDEXES = [
    ("estudiantes", "idx_estudiantes_curso_id", ["curso_id"]),
    ("pagos", "idx_pagos_estudiante_id", ["estudiante_id"]),
    ("pagos", "idx_pagos_fecha", ["fecha"]),
    ("pagos", "idx_pagos_fecha_pago", ["fecha_pago"]),
    ("asistencia", "idx_asistencia_estudiante_fecha", ["estudiante_id", "fecha"]),
    ("asistencia", "idx_asistencia_asignacion_periodo", ["asignacion_id", "periodo"]),
    ("notas_detalle", "idx_notas_detalle_estudiante_asignacion_periodo", ["estudiante_id", "asignacion_id", "periodo"]),
    ("boletin_cabecera", "idx_boletin_cabecera_lookup", ["estudiante_id", "asignacion_id", "periodo"]),
    ("asignaciones", "idx_asignaciones_curso_id", ["curso_id"]),
    ("asignaciones", "idx_asignaciones_profesor_id", ["profesor_id"]),
    ("ventas", "idx_ventas_estudiante_estado", ["estudiante_id", "estado"]),
    ("plan_de_clases", "idx_plan_de_clases_asignacion_fecha", ["asignacion_id", "fecha"]),
    # Bitacora del observador: todas las anotaciones de un estudiante, la mas
    # nueva primero. Basta con orden ascendente: un indice btree se recorre en
    # ambos sentidos, y aqui estudiante_id es constante, asi que sirve igual a
    # ORDER BY creada_en DESC.
    ("observador_anotaciones", "idx_observador_anotaciones_estudiante", ["estudiante_id", "creada_en"]),
]


def fetch_tenants(cursor):
    cursor.execute("""
        SELECT esquema_db
        FROM public.colegios
        WHERE LOWER(estado) IN ('activo', 'en_mora')
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


def columns_exist(cursor, schema, table, columns):
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
    """, (schema, table))
    existing_columns = {row[0] for row in cursor.fetchall()}
    return all(column in existing_columns for column in columns)


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


def apply_indexes(dry_run=False):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no esta configurado")

    conn = psycopg2.connect(database_url)
    try:
        conn.autocommit = False
        cursor = conn.cursor()
        tenants = fetch_tenants(cursor)

        mode = "simulando" if dry_run else "verificando"
        print(f"\n>> {mode} indices en {len(tenants)} tenant(s)...\n")

        for schema in tenants:
            for table, index_name, columns in INDEXES:
                if table_exists(cursor, schema, table):
                    if not columns_exist(cursor, schema, table, columns):
                        print(f"{schema}.{table}: columnas {', '.join(columns)} no existen, omitido")
                        continue

                    if dry_run:
                        print(f"{schema}.{table}: indice {index_name} pendiente de verificacion")
                        continue

                    create_index(cursor, schema, table, index_name, columns)
                    print(f"{schema}.{table}: indice {index_name} verificado")
                else:
                    print(f"{schema}.{table}: tabla no existe, omitida")

        if dry_run:
            conn.rollback()
            print("\n>> Simulacion completada. No se crearon indices.")
        else:
            conn.commit()
            print("\n>> Indices verificados en todos los tenants operativos.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Crea/verifica indices recomendados en todos los tenants operativos.")
    parser.add_argument("--dry-run", action="store_true", help="Muestra que indices se revisarian sin crearlos")
    args = parser.parse_args()
    apply_indexes(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
