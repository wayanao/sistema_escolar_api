import os
from collections import defaultdict

import psycopg2
from dotenv import load_dotenv


load_dotenv()


def fetch_tenants(cursor):
    cursor.execute("""
        SELECT esquema_db
        FROM public.colegios
        WHERE LOWER(estado) IN ('activo', 'en_mora')
        ORDER BY esquema_db
    """)
    return [row[0] for row in cursor.fetchall()]


def fetch_columns(cursor, schema):
    cursor.execute("""
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s
        ORDER BY table_name, ordinal_position
    """, (schema,))
    columns = defaultdict(list)
    for table_name, column_name, data_type, is_nullable in cursor.fetchall():
        columns[table_name].append((column_name, data_type, is_nullable))
    return dict(columns)


def fetch_indexes(cursor, schema):
    cursor.execute("""
        SELECT tablename, indexname
        FROM pg_indexes
        WHERE schemaname = %s
        ORDER BY tablename, indexname
    """, (schema,))
    indexes = defaultdict(set)
    for table_name, index_name in cursor.fetchall():
        indexes[table_name].add(index_name)
    return dict(indexes)


def compare_schema(template_schema, target_schema, template_columns, target_columns):
    differences = []
    template_tables = set(template_columns)
    target_tables = set(target_columns)

    for table in sorted(template_tables - target_tables):
        differences.append(f"{target_schema}: falta tabla {table}")

    for table in sorted(target_tables - template_tables):
        differences.append(f"{target_schema}: tabla extra {table}")

    for table in sorted(template_tables & target_tables):
        template_table_columns = set(template_columns[table])
        target_table_columns = set(target_columns[table])
        for column in sorted(template_table_columns - target_table_columns):
            differences.append(f"{target_schema}.{table}: falta columna {column[0]}")
        for column in sorted(target_table_columns - template_table_columns):
            differences.append(f"{target_schema}.{table}: columna extra/diferente {column[0]}")

    if not differences:
        differences.append(f"{target_schema}: OK contra {template_schema}")

    return differences


def main():
    database_url = os.getenv("DATABASE_URL")
    template_schema = os.getenv("DEFAULT_TENANT_SCHEMA", "tenant_colegio_1")

    if not database_url:
        raise RuntimeError("DATABASE_URL no esta configurado")

    conn = psycopg2.connect(database_url)
    try:
        cursor = conn.cursor()
        tenants = fetch_tenants(cursor)

        if template_schema not in tenants:
            tenants.insert(0, template_schema)

        template_columns = fetch_columns(cursor, template_schema)
        template_indexes = fetch_indexes(cursor, template_schema)

        print(f"Template: {template_schema}")
        print(f"Tenants revisados: {', '.join(tenants)}")
        print()

        for tenant_schema in tenants:
            target_columns = fetch_columns(cursor, tenant_schema)
            for line in compare_schema(template_schema, tenant_schema, template_columns, target_columns):
                print(line)

            target_indexes = fetch_indexes(cursor, tenant_schema)
            missing_index_tables = sorted(set(template_indexes) - set(target_indexes))
            if missing_index_tables:
                print(f"{tenant_schema}: revisar indices en tablas {', '.join(missing_index_tables)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
