"""Aplica un archivo SQL de migracion en todos los schemas tenant activos.

Uso:
    python apply_migration.py migrations/20260509_branding_plantillas_impresion.sql

El archivo SQL se ejecuta dentro de una transaccion por tenant. Si falla,
se revierte el tenant entero (los demas siguen su curso si ya se aplicaron).
"""
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


def apply_migration(sql_path: Path) -> int:
    if not sql_path.exists():
        print(f"X No existe el archivo: {sql_path}")
        return 1

    sql_text = sql_path.read_text(encoding="utf-8")

    load_dotenv(Path(__file__).parent / ".env")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("X DATABASE_URL no esta definido en .env")
        return 1

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute("""
        SELECT esquema_db, nombre
        FROM public.colegios
        WHERE estado = 'activo'
        ORDER BY id
    """)
    tenants = cur.fetchall()
    cur.close()

    if not tenants:
        print("! No hay tenants activos. Nada que aplicar.")
        conn.close()
        return 0

    print(f"\n>> Aplicando '{sql_path.name}' en {len(tenants)} tenant(s)...\n")

    fallos = 0
    for esquema, nombre in tenants:
        cur = conn.cursor()
        try:
            print(f"  -> {esquema} ({nombre}) ... ", end="", flush=True)
            # Apuntamos el search_path para que CREATE/INSERT vayan al schema correcto.
            cur.execute(f'SET search_path TO "{esquema}", public;')
            cur.execute(sql_text)
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
    print("\n>> Migracion aplicada en todos los tenants activos.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python apply_migration.py <ruta_al_archivo.sql>")
        raise SystemExit(1)
    raise SystemExit(apply_migration(Path(sys.argv[1])))
