"""Cuenta las filas de `observaciones` que impedirian reponer sus claves foraneas.

Uso:
    python scripts/auditar_huerfanos_observaciones.py

Es un **informe, no una correccion**. Abre la transaccion como READ ONLY, no
escribe nada y termina con rollback, siguiendo el criterio que la capa 4 fijo
para toda medicion contra produccion.

Sirve para responder, **antes** de tocar el esquema, la unica pregunta que puede
hacer fallar a `migrations/20260825_observaciones_claves_foraneas.sql`: si hay
observaciones apuntando a un estudiante o a una asignacion que ya no existen.
Esa migracion se detiene con el recuento si las encuentra, asi que este script
adelanta la respuesta sin intentar el cambio.

Recorre **todos los schemas de tenant**, no solo el de produccion, porque el
runner aplica la migracion a todos y basta uno con huerfanos para detenerla.

Codigos de salida:
    0  ningun huerfano: la migracion puede aplicarse.
    1  error de configuracion.
    2  hay huerfanos en al menos un schema: revision manual antes de aplicar.
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]


CONSULTA_HUERFANOS = """
    SELECT
        (SELECT COUNT(*) FROM observaciones o
          WHERE o.estudiante_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM estudiantes e WHERE e.id = o.estudiante_id)),
        (SELECT COUNT(*) FROM observaciones o
          WHERE o.asignacion_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM asignaciones a WHERE a.id = o.asignacion_id)),
        (SELECT COUNT(*) FROM observaciones WHERE estudiante_id IS NULL),
        (SELECT COUNT(*) FROM observaciones WHERE asignacion_id IS NULL),
        (SELECT COUNT(*) FROM observaciones)
"""

CONSULTA_CLAVES = """
    SELECT conname
    FROM pg_constraint
    WHERE conrelid = 'observaciones'::regclass AND contype = 'f'
    ORDER BY conname
"""


def listar_schemas_tenant(cursor):
    cursor.execute(
        """
        SELECT nspname
        FROM pg_namespace
        WHERE nspname LIKE 'tenant\\_%'
        ORDER BY nspname
        """
    )
    return [fila[0] for fila in cursor.fetchall()]


def tabla_existe(cursor, schema):
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = 'observaciones'
        """,
        (schema,),
    )
    return cursor.fetchone() is not None


def auditar(cursor, schema):
    cursor.execute(f'SET search_path TO "{schema}"')
    cursor.execute(CONSULTA_HUERFANOS)
    est, asig, est_nulos, asig_nulos, total = cursor.fetchone()
    cursor.execute(CONSULTA_CLAVES)
    claves = [fila[0] for fila in cursor.fetchall()]
    return {
        "schema": schema,
        "total": total,
        "estudiantes_huerfanos": est,
        "asignaciones_huerfanas": asig,
        "estudiante_id_nulos": est_nulos,
        "asignacion_id_nulos": asig_nulos,
        "claves_foraneas": claves,
    }


def main():
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("X DATABASE_URL no esta definido en .env")
        return 1

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        cursor.execute("SET TRANSACTION READ ONLY")

        schemas = listar_schemas_tenant(cursor)
        if not schemas:
            print("X No se encontro ningun schema de tenant.")
            return 1

        print(f"Revisando `observaciones` en {len(schemas)} schema(s) de tenant...\n")

        con_huerfanos = []
        for schema in schemas:
            if not tabla_existe(cursor, schema):
                print(f"  {schema}: sin tabla `observaciones`, se omite")
                continue

            r = auditar(cursor, schema)
            marca = "!" if (r["estudiantes_huerfanos"] or r["asignaciones_huerfanas"]) else "OK"
            print(f"  [{marca}] {schema}: {r['total']} fila(s)")
            print(
                f"        estudiante_id huerfano : {r['estudiantes_huerfanos']}"
                f"   |  nulo: {r['estudiante_id_nulos']}"
            )
            print(
                f"        asignacion_id huerfano : {r['asignaciones_huerfanas']}"
                f"   |  nulo: {r['asignacion_id_nulos']}"
            )
            print(
                f"        claves foraneas actuales: "
                f"{', '.join(r['claves_foraneas']) if r['claves_foraneas'] else 'ninguna'}"
            )

            if r["estudiantes_huerfanos"] or r["asignaciones_huerfanas"]:
                con_huerfanos.append(r)

        print()
        if con_huerfanos:
            print(
                f"! {len(con_huerfanos)} schema(s) con filas huerfanas. La migracion "
                "se detendria: hay que decidir que hacer con ellas antes de aplicarla."
            )
            print("  Este script NO las borra ni las modifica.")
            return 2

        print(
            "Ningun huerfano. La migracion de claves foraneas puede aplicarse "
            "sin revision manual previa."
        )
        print(
            "Recordatorio: una clave foranea no restringe NULL, asi que las filas "
            "con columna nula seguiran siendo validas."
        )
        return 0
    finally:
        conn.rollback()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
