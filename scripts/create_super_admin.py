import argparse
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.security import get_password_hash


ENSURE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public.super_admins (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'activo',
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_super_admins_estado
ON public.super_admins (estado);
"""


def create_or_update_super_admin(nombre: str, email: str, password: str) -> int:
    load_dotenv()
    conn = psycopg2.connect(settings.DATABASE_URL)
    cursor = conn.cursor()
    try:
        cursor.execute(ENSURE_TABLE_SQL)
        cursor.execute(
            """
            INSERT INTO public.super_admins (nombre, email, password, estado)
            VALUES (%s, %s, %s, 'activo')
            ON CONFLICT (email)
            DO UPDATE SET
                nombre = EXCLUDED.nombre,
                password = EXCLUDED.password,
                estado = 'activo'
            RETURNING id
            """,
            (nombre.strip(), email.strip().lower(), get_password_hash(password)),
        )
        super_admin_id = cursor.fetchone()[0]
        conn.commit()
        return super_admin_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crea o actualiza el super admin de plataforma.")
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    user_id = create_or_update_super_admin(args.nombre, args.email, args.password)
    print(f"Super admin listo con id {user_id}. Codigo de colegio para login: super_admin")
