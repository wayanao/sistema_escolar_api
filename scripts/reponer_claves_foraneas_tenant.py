"""Repone en un tenant las claves foraneas que la plantilla tiene y a el le faltan.

Uso:
    python scripts/reponer_claves_foraneas_tenant.py --schema tenant_2005 --dry-run
    python scripts/reponer_claves_foraneas_tenant.py --schema tenant_2005

El alta de tenants copiaba la estructura con LIKE INCLUDING ALL, que reproduce
columnas, indices, PRIMARY KEY, UNIQUE y CHECK, pero **no** las claves foraneas.
Los tenants creados asi quedaron sin integridad referencial en las tablas que ya
existian antes de la copia.

Antes de crear nada cuenta las filas huerfanas de cada clave y se niega si
encuentra alguna: crear la clave fallaria a mitad y no tiene sentido intentarlo.
Todo ocurre en una sola transaccion; si algo falla, no queda nada a medias.

Las definiciones se toman de la plantilla con el search_path apuntando a ella,
de modo que salen sin cualificar y se aplican tal cual en el schema destino,
conservando ON DELETE y ON UPDATE.
"""
import argparse
import os
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]

CONSULTA_FK = """
SELECT rel.relname,
       ARRAY(SELECT a.attname FROM unnest(con.conkey) k
             JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k),
       ref.relname,
       ARRAY(SELECT a.attname FROM unnest(con.confkey) k
             JOIN pg_attribute a ON a.attrelid = con.confrelid AND a.attnum = k),
       con.conname,
       pg_get_constraintdef(con.oid)
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
JOIN pg_class ref ON ref.oid = con.confrelid
JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
WHERE nsp.nspname = %s AND con.contype = 'f'
ORDER BY rel.relname, con.conname
"""


def leer_claves(cursor, schema):
    cursor.execute(CONSULTA_FK, (schema,))
    return [
        {
            "tabla": tabla,
            "columnas": list(columnas),
            "tabla_ref": tabla_ref,
            "columnas_ref": list(columnas_ref),
            "nombre": nombre,
            "definicion": definicion,
        }
        for tabla, columnas, tabla_ref, columnas_ref, nombre, definicion in cursor.fetchall()
    ]


def identidad(clave):
    return (clave["tabla"], tuple(clave["columnas"]), clave["tabla_ref"])


def claves_ausentes(cursor, plantilla, destino):
    presentes = {identidad(c) for c in leer_claves(cursor, destino)}
    return [c for c in leer_claves(cursor, plantilla) if identidad(c) not in presentes]


def contar_huerfanos(cursor, schema, clave):
    """Filas hijas cuya referencia no existe en la tabla padre."""
    if len(clave["columnas"]) != 1:
        return None
    columna, columna_ref = clave["columnas"][0], clave["columnas_ref"][0]
    cursor.execute(
        sql.SQL(
            """
            SELECT COUNT(*) FROM {}.{} hijo
            WHERE hijo.{} IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM {}.{} padre WHERE padre.{} = hijo.{}
              )
            """
        ).format(
            sql.Identifier(schema), sql.Identifier(clave["tabla"]),
            sql.Identifier(columna),
            sql.Identifier(schema), sql.Identifier(clave["tabla_ref"]),
            sql.Identifier(columna_ref), sql.Identifier(columna),
        )
    )
    return cursor.fetchone()[0]


def crear_clave(cursor, schema, clave):
    """Crea la clave en `schema`.

    La definicion viene SIN cualificar (`REFERENCES cursos(id)`), asi que
    PostgreSQL resuelve la tabla padre con el search_path vigente. Hay que
    apuntarlo al schema destino antes de llamar aqui: con el search_path en la
    plantilla, la clave apuntaria a las tablas de la plantilla y se crearia un
    acoplamiento entre schemas.
    """
    cursor.execute(
        sql.SQL("ALTER TABLE {}.{} ADD CONSTRAINT {} {}").format(
            sql.Identifier(schema),
            sql.Identifier(clave["tabla"]),
            sql.Identifier(clave["nombre"]),
            sql.SQL(clave["definicion"]),
        )
    )


def claves_que_apuntan_fuera(cursor, schema):
    """Claves del schema cuya tabla padre vive en otro schema.

    Guarda contra el error que se cometio al escribir este script: si el
    search_path apunta a otro sitio al crearlas, las claves salen cruzadas.
    """
    cursor.execute(
        """
        SELECT rel.relname, con.conname, nsp_ref.nspname
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        JOIN pg_class ref ON ref.oid = con.confrelid
        JOIN pg_namespace nsp_ref ON nsp_ref.oid = ref.relnamespace
        WHERE nsp.nspname = %s AND con.contype = 'f' AND nsp_ref.nspname <> %s
        ORDER BY rel.relname, con.conname
        """,
        (schema, schema),
    )
    return cursor.fetchall()


def main(schema: str, plantilla: str, dry_run: bool = False) -> int:
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("X DATABASE_URL no esta definido en .env")
        return 1
    if schema == plantilla:
        print("X El schema destino no puede ser la propia plantilla")
        return 1

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        # Con el search_path en la plantilla, pg_get_constraintdef omite el
        # schema y la definicion sirve tal cual para el destino.
        cursor.execute(
            sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(plantilla))
        )
        ausentes = claves_ausentes(cursor, plantilla, schema)
        if not ausentes:
            print(f"Nada que reponer: {schema} ya tiene las claves de {plantilla}.")
            conn.rollback()
            return 0

        print(f"\n>> {schema}: {len(ausentes)} clave(s) foranea(s) ausente(s)\n")
        bloqueantes = []
        for clave in ausentes:
            huerfanos = contar_huerfanos(cursor, schema, clave)
            if huerfanos is None:
                bloqueantes.append((clave["nombre"], "clave compuesta, sin comprobar"))
                estado = "compuesta"
            elif huerfanos:
                bloqueantes.append((clave["nombre"], f"{huerfanos} fila(s) huerfana(s)"))
                estado = f"{huerfanos} HUERFANAS"
            else:
                estado = "sin huerfanos"
            print(
                f'  {clave["tabla"]}.{",".join(clave["columnas"])} -> '
                f'{clave["tabla_ref"]}  [{estado}]'
            )
            print(f'      {clave["definicion"]}')

        if bloqueantes:
            print(f"\n!! {len(bloqueantes)} clave(s) no se pueden crear tal cual:")
            for nombre, motivo in bloqueantes:
                print(f"  - {nombre}: {motivo}")
            print("   No se creo ninguna. Hay que resolver esas filas primero.")
            conn.rollback()
            return 2

        if dry_run:
            print("\n>> Simulacion: no se creo ninguna clave.")
            conn.rollback()
            return 0

        # Imprescindible: las definiciones no llevan schema, asi que la tabla
        # padre se resuelve con el search_path. Debe apuntar al destino.
        cursor.execute(
            sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema))
        )
        for clave in ausentes:
            crear_clave(cursor, schema, clave)

        cruzadas = claves_que_apuntan_fuera(cursor, schema)
        if cruzadas:
            conn.rollback()
            print(f"\n!! {len(cruzadas)} clave(s) quedaron apuntando a otro schema:")
            for tabla, nombre, destino_ref in cruzadas:
                print(f"  - {tabla}.{nombre} -> {destino_ref}")
            print("   Se revirtio todo.")
            return 2

        cursor.execute(
            sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(plantilla))
        )
        restantes = claves_ausentes(cursor, plantilla, schema)
        if restantes:
            conn.rollback()
            print(f"\n!! Quedaron {len(restantes)} sin crear. Se revirtio todo.")
            return 2

        conn.commit()
        print(f"\n>> Creadas {len(ausentes)} clave(s) foranea(s) en {schema}.")
        return 0
    except Exception as exc:
        conn.rollback()
        print(f"\n!! FALLO ({type(exc).__name__}: {exc}). Se revirtio todo.")
        return 2
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Repone las claves foraneas que la plantilla tiene y el tenant no."
    )
    parser.add_argument("--schema", required=True, help="Schema del tenant")
    parser.add_argument(
        "--plantilla",
        default=os.getenv("DEFAULT_TENANT_SCHEMA", "tenant_colegio_1"),
        help="Schema de referencia del que se copian las definiciones",
    )
    parser.add_argument("--dry-run", action="store_true", help="Muestra sin crear")
    args = parser.parse_args()
    raise SystemExit(main(args.schema, args.plantilla, dry_run=args.dry_run))
