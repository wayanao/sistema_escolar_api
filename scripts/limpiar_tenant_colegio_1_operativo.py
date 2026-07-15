"""Limpia datos operativos de tenant_colegio_1 conservando plantilla y admin.

No borra schema ni tablas. Conserva usuarios, branding, plantillas y catalogos base.
Genera respaldo JSONL.GZ de las tablas que se van a vaciar antes de truncarlas.
"""
import gzip
import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

SCHEMA = "tenant_colegio_1"
EXPECTED_COLLEGE = "Colegio Demo"

PRESERVED_TABLES = {
    "usuarios",
    "institucion_branding",
    "plantilla_impresion",
    "cursos",
    "materias",
    "tipos_de_pagos",
    "tipos_pagos_cursos",
}

CLEAN_TABLES = [
    "boletin_detalles",
    "boletin_cabecera",
    "asistencia",
    "notas",
    "notas_detalle",
    "observaciones",
    "plan_de_clases",
    "planeador_anual",
    "pagos",
    "ventas_detalle",
    "ventas",
    "tipos_pagos_estudiantes",
    "matriculas",
    "nomina",
    "prestamos",
    "egresos",
    "inventario",
    "asignaciones",
    "estudiantes",
    "profesor",
]


def json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def fetch_count(cur, table):
    cur.execute(
        sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
            sql.Identifier(SCHEMA),
            sql.Identifier(table),
        )
    )
    return cur.fetchone()[0]


def dump_table(cur, backup, table):
    cur.execute(
        sql.SQL("SELECT * FROM {}.{}").format(
            sql.Identifier(SCHEMA),
            sql.Identifier(table),
        )
    )
    columns = [desc[0] for desc in cur.description]
    backup.write(json.dumps({"type": "table_start", "table": table, "columns": columns}) + "\n")
    rows = 0
    for row in cur.fetchall():
        backup.write(
            json.dumps(
                {"type": "row", "table": table, "data": dict(zip(columns, row))},
                default=json_default,
                ensure_ascii=False,
            )
            + "\n"
        )
        rows += 1
    backup.write(json.dumps({"type": "table_end", "table": table, "rows": rows}) + "\n")
    return rows


def main():
    project_dir = Path(__file__).resolve().parents[1]
    load_dotenv(project_dir / ".env")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit("DATABASE_URL no esta definido")

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT id, nombre, esquema_db, estado FROM public.colegios WHERE esquema_db = %s",
            (SCHEMA,),
        )
        colegio = cur.fetchone()
        if not colegio:
            raise RuntimeError(f"No existe public.colegios para {SCHEMA}")
        if colegio[1] != EXPECTED_COLLEGE:
            raise RuntimeError(f"El colegio no coincide: {colegio}")

        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            """,
            (SCHEMA,),
        )
        existing_tables = {row[0] for row in cur.fetchall()}
        missing = [table for table in CLEAN_TABLES if table not in existing_tables]
        if missing:
            raise RuntimeError(f"Tablas esperadas no existen en {SCHEMA}: {missing}")
        forbidden = [table for table in CLEAN_TABLES if table in PRESERVED_TABLES]
        if forbidden:
            raise RuntimeError(f"La lista de limpieza intenta tocar tablas preservadas: {forbidden}")

        before_clean = {table: fetch_count(cur, table) for table in CLEAN_TABLES}
        before_preserved = {table: fetch_count(cur, table) for table in sorted(PRESERVED_TABLES)}

        backup_dir = project_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{SCHEMA}_datos_operativos_{stamp}.jsonl.gz"

        with gzip.open(backup_path, "wt", encoding="utf-8") as backup:
            backup.write(
                json.dumps(
                    {
                        "type": "metadata",
                        "schema": SCHEMA,
                        "colegio": colegio,
                        "created_at": datetime.now().isoformat(),
                        "clean_tables": CLEAN_TABLES,
                        "preserved_tables": sorted(PRESERVED_TABLES),
                        "before_clean": before_clean,
                        "before_preserved": before_preserved,
                    },
                    default=json_default,
                    ensure_ascii=False,
                )
                + "\n"
            )
            for table in CLEAN_TABLES:
                dump_table(cur, backup, table)

        cur.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(SCHEMA)))
        truncate_targets = sql.SQL(", ").join(
            sql.SQL("{}.{}").format(sql.Identifier(SCHEMA), sql.Identifier(table))
            for table in CLEAN_TABLES
        )
        cur.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY").format(truncate_targets))

        after_clean = {table: fetch_count(cur, table) for table in CLEAN_TABLES}
        after_preserved = {table: fetch_count(cur, table) for table in sorted(PRESERVED_TABLES)}

        if any(count != 0 for count in after_clean.values()):
            raise RuntimeError(f"Algunas tablas operativas no quedaron vacias: {after_clean}")
        if before_preserved != after_preserved:
            raise RuntimeError(
                f"Cambio inesperado en tablas preservadas. Antes={before_preserved} Despues={after_preserved}"
            )

        conn.commit()

        print("OK limpieza tenant_colegio_1")
        print(f"backup={backup_path}")
        print(f"filas_limpiadas={sum(before_clean.values())}")
        print("tablas_limpiadas=")
        for table, count in before_clean.items():
            print(f"  {table}: {count} -> {after_clean[table]}")
        print("tablas_preservadas=")
        for table, count in after_preserved.items():
            print(f"  {table}: {count}")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
