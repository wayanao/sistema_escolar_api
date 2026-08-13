"""Aplica un archivo SQL de migracion en todos los schemas tenant operativos.

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


"""Clave fija del advisory lock que serializa las ejecuciones del runner.

Es un entero de 64 bits arbitrario pero estable. Cambiarlo permitiria que dos
ejecuciones se tomen locks distintos y anularia la proteccion.
"""
MIGRATION_LOCK_KEY = 8274119453012006001


def calculate_checksum(sql_text: str) -> str:
    return hashlib.sha256(sql_text.encode("utf-8")).hexdigest()


def es_endpoint_agrupado(dsn: str) -> bool:
    """Detecta el endpoint agrupado de Neon, que es PgBouncer.

    Sobre el pooler, dos conexiones distintas obtienen el mismo advisory lock de
    sesion: se comprobo contra PostgreSQL 17 y la exclusion mutua no se sostiene.
    Ejecutar migraciones por ahi daria una falsa sensacion de proteccion.
    """
    host = dsn.split("@", 1)[-1].split("/", 1)[0]
    return "-pooler" in host


def try_acquire_migration_lock(cursor) -> bool:
    """Toma el lock que impide dos ejecuciones simultaneas del runner.

    Devuelve False si otra ejecucion ya lo tiene. El lock es de sesion, no de
    transaccion: sobrevive a los commit y rollback por tenant y PostgreSQL lo
    libera solo cuando la conexion se cierra.
    """
    cursor.execute("SELECT pg_try_advisory_lock(%s)", (MIGRATION_LOCK_KEY,))
    row = cursor.fetchone()
    return bool(row and row[0])


def ensure_migration_history(cursor) -> None:
    cursor.execute(MIGRATION_HISTORY_SQL)


def fetch_active_tenants(cursor):
    cursor.execute("""
        SELECT esquema_db, nombre
        FROM public.colegios
        WHERE LOWER(estado) IN ('activo', 'en_mora')
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


def is_public_migration(sql_path: Path) -> bool:
    return sql_path.parent.name == "public"


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

    if es_endpoint_agrupado(db_url):
        print(
            "X DATABASE_URL apunta al endpoint agrupado (-pooler), que es PgBouncer.\n"
            "  El lock que impide dos ejecuciones simultaneas no se sostiene ahi.\n"
            "  Usa el endpoint directo, sin '-pooler' en el host."
        )
        return 1

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    # El lock se toma antes de cualquier lectura o escritura del historial para
    # que dos ejecuciones no lleguen a decidir sobre el mismo tenant.
    if not try_acquire_migration_lock(cur):
        print("X Ya hay otra ejecucion de migraciones en curso. No se aplico nada.")
        cur.close()
        conn.close()
        return 2

    ensure_migration_history(cur)
    if is_public_migration(sql_path):
        try:
            record = get_migration_record(cur, sql_path.name, "public")
            if record:
                if record[0] != checksum:
                    print("X Migracion publica con mismo nombre y checksum diferente")
                    conn.rollback()
                    return 2
                print("OMITIDA (migracion publica ya aplicada)")
                conn.rollback()
                return 0

            if dry_run:
                print(f"PENDIENTE public/{sql_path.name}")
                conn.rollback()
                return 0

            cur.execute("SET search_path TO public")
            cur.execute(sql_text)
            record_migration(cur, sql_path.name, "public", checksum)
            conn.commit()
            print(f"OK public/{sql_path.name}")
            return 0
        except Exception as exc:
            conn.rollback()
            print(f"FALLO public/{sql_path.name} ({type(exc).__name__}: {exc})")
            return 2
        finally:
            cur.close()
            conn.close()

    tenants = fetch_active_tenants(cur)
    conn.commit()
    cur.close()

    if not tenants:
        print("! No hay tenants operativos. Nada que aplicar.")
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
        print("\n>> Migracion aplicada en todos los tenants operativos.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aplica una migracion SQL a todos los tenants operativos.")
    parser.add_argument("sql_path", help="Ruta al archivo SQL de migracion")
    parser.add_argument("--dry-run", action="store_true", help="Muestra que tenants recibirian la migracion sin aplicarla")
    args = parser.parse_args()

    raise SystemExit(apply_migration(Path(args.sql_path), dry_run=args.dry_run))
