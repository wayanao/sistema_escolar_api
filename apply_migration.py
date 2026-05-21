"""Aplica un archivo SQL de migracion en todos los schemas tenant activos.

Uso:
    python apply_migration.py migrations/20260509_branding_plantillas_impresion.sql
    python apply_migration.py migrations/20260509_branding_plantillas_impresion.sql --dry-run

El archivo SQL se ejecuta dentro de una transaccion por tenant. Si falla,
se revierte el tenant entero (los demas siguen su curso si ya se aplicaron).
"""
import argparse
import hashlib
import os
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


MIGRATION_HISTORY_SQL = """
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name TEXT NOT NULL,
    target_schema TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (migration_name, target_schema)
)
"""


def calculate_checksum(sql_text: str) -> str:
    return hashlib.sha256(sql_text.encode("utf-8")).hexdigest()


def ensure_migration_history(cursor) -> None:
    cursor.execute(MIGRATION_HISTORY_SQL)


def fetch_active_tenants(cursor):
    cursor.execute("""
        SELECT esquema_db, nombre
        FROM public.colegios
        WHERE estado = 'activo'
        ORDER BY id
    """)
    return cursor.fetchall()


def get_migration_record(cursor, migration_name: str, target_schema: str):
    cursor.execute(
        """
        SELECT checksum
        FROM public.schema_migrations
        WHERE migration_name = %s AND target_schema = %s
        """,
        (migration_name, target_schema),
    )
    return cursor.fetchone()


def record_migration(cursor, migration_name: str, target_schema: str, checksum: str) -> None:
    cursor.execute(
        """
        INSERT INTO public.schema_migrations (migration_name, target_schema, checksum)
        VALUES (%s, %s, %s)
        """,
        (migration_name, target_schema, checksum),
    )


def apply_migration(sql_path: Path, dry_run: bool = False) -> int:
    if not sql_path.exists():
        print(f"X No existe el archivo: {sql_path}")
        return 1

    sql_text = sql_path.read_text(encoding="utf-8")
    checksum = calculate_checksum(sql_text)

    load_dotenv(Path(__file__).parent / ".env")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("X DATABASE_URL no esta definido en .env")
        return 1

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    ensure_migration_history(cur)
    tenants = fetch_active_tenants(cur)
    conn.commit()
    cur.close()

    if not tenants:
        print("! No hay tenants activos. Nada que aplicar.")
        conn.close()
        return 0

    modo = "simulando" if dry_run else "aplicando"
    print(f"\n>> {modo} '{sql_path.name}' en {len(tenants)} tenant(s)...\n")

    fallos = 0
    for esquema, nombre in tenants:
        cur = conn.cursor()
        try:
            print(f"  -> {esquema} ({nombre}) ... ", end="", flush=True)

            record = get_migration_record(cur, sql_path.name, esquema)
            if record:
                if record[0] != checksum:
                    fallos += 1
                    print("FALLO (mismo nombre con checksum diferente)")
                    conn.rollback()
                    continue

                print("OMITIDA (ya aplicada)")
                conn.rollback()
                continue

            if dry_run:
                print("PENDIENTE")
                conn.rollback()
                continue

            # Apuntamos el search_path para que CREATE/INSERT vayan al schema correcto.
            cur.execute(
                sql.SQL("SET search_path TO {}, public").format(sql.Identifier(esquema))
            )
            cur.execute(sql_text)
            record_migration(cur, sql_path.name, esquema, checksum)
            conn.commit()
            print("OK")
        except Exception as exc:
            conn.rollback()
            fallos += 1
            print(f"FALLO ({type(exc).__name__}: {exc})")
        finally:
            cur.close()

    conn.close()

    if fallos:
        print(f"\n!! Migracion completo con {fallos} fallo(s).")
        return 2
    if dry_run:
        print("\n>> Simulacion completada. No se aplicaron cambios.")
    else:
        print("\n>> Migracion aplicada en todos los tenants activos.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aplica una migracion SQL a todos los tenants activos.")
    parser.add_argument("sql_path", help="Ruta al archivo SQL de migracion")
    parser.add_argument("--dry-run", action="store_true", help="Muestra que tenants recibirian la migracion sin aplicarla")
    args = parser.parse_args()

    raise SystemExit(apply_migration(Path(args.sql_path), dry_run=args.dry_run))
