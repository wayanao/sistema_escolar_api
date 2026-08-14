"""Regenera la migracion base de un tenant a partir de un schema real.

Uso:
    python scripts/generar_esquema_base.py --schema tenant_colegio_1

El alta de colegios nuevos no aplica las migraciones una por una: aplica un
unico archivo con el esquema completo. Ese archivo hay que rehacerlo cada vez
que se anade una migracion, o los colegios nuevos naceran con la estructura
vieja. Este script hace ese trabajo en un comando.

**Ejecutalo DESPUES de aplicar la migracion al schema de referencia**, no antes:
lee la estructura real, asi que si el schema todavia no la tiene, capturara el
esquema anterior sin avisar.

Es de solo lectura sobre la base: abre la transaccion como READ ONLY y termina
con rollback. Lo unico que escribe es el archivo .sql.

El archivo generado declara en su cabecera que migraciones incorpora, tomadas de
public.schema_migrations para ese schema. `tests/test_esquema_base.py` compara
esa lista con el contenido de migrations/ y falla si alguien anadio una
migracion y no regenero la base.
"""
import argparse
import os
from datetime import date
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
SALIDA_POR_DEFECTO = ROOT_DIR / "migrations" / "base" / "20260813_esquema_base_tenant.sql"

SERIALES = {"integer": "SERIAL", "bigint": "BIGSERIAL", "smallint": "SMALLSERIAL"}


def tablas(cursor, schema):
    cursor.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = %s ORDER BY tablename",
        (schema,),
    )
    return [fila[0] for fila in cursor.fetchall()]


def columnas(cursor, schema, tabla):
    cursor.execute(
        """
        SELECT a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull,
               pg_get_expr(d.adbin, d.adrelid)
        FROM pg_attribute a
        LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relname = %s
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum
        """,
        (schema, tabla),
    )
    return cursor.fetchall()


def restricciones(cursor, schema, tabla, tipos):
    cursor.execute(
        """
        SELECT con.conname, pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = %s AND rel.relname = %s AND con.contype = ANY(%s)
        ORDER BY con.contype, con.conname
        """,
        (schema, tabla, list(tipos)),
    )
    return cursor.fetchall()


def indices_sueltos(cursor, schema, tabla):
    """Indices que no respaldan una restriccion; esos vienen con la restriccion."""
    cursor.execute(
        """
        SELECT pg_get_indexdef(i.indexrelid)
        FROM pg_index i
        JOIN pg_class c ON c.oid = i.indrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relname = %s
          AND NOT EXISTS (
              SELECT 1 FROM pg_constraint con WHERE con.conindid = i.indexrelid
          )
        ORDER BY i.indexrelid::regclass::text
        """,
        (schema, tabla),
    )
    return [fila[0] for fila in cursor.fetchall()]


def funciones(cursor, schema):
    cursor.execute(
        """
        SELECT pg_get_functiondef(p.oid)
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = %s AND p.prokind = 'f'
        ORDER BY p.proname
        """,
        (schema,),
    )
    return [fila[0] for fila in cursor.fetchall()]


def disparadores(cursor, schema):
    cursor.execute(
        """
        SELECT pg_get_triggerdef(t.oid)
        FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND NOT t.tgisinternal
        ORDER BY t.tgname
        """,
        (schema,),
    )
    return [fila[0] for fila in cursor.fetchall()]


def migraciones_incorporadas(cursor, schema):
    cursor.execute(
        """
        SELECT migration_name FROM public.schema_migrations
        WHERE target_schema = %s ORDER BY migration_name
        """,
        (schema,),
    )
    return [fila[0] for fila in cursor.fetchall()]


def definicion_columna(nombre, tipo, notnull, default):
    """Las columnas con nextval se emiten como SERIAL para que cada schema cree
    su PROPIA secuencia. Copiar el DEFAULT original las haria apuntar a las del
    schema de referencia, que es el defecto que la capa 3 tuvo que reparar."""
    if default and "nextval(" in default:
        serial = SERIALES.get(tipo)
        if serial:
            return f"    {nombre} {serial}"
    partes = [f"    {nombre} {tipo}"]
    if default:
        partes.append(f"DEFAULT {default}")
    if notnull:
        partes.append("NOT NULL")
    return " ".join(partes)


def cabecera(schema, incorporadas, generado_el):
    lineas = [
        "-- Esquema base de un tenant. ARCHIVO GENERADO, no editar a mano.",
        "--",
        f"-- Extraido de {schema} el {generado_el} con",
        "-- scripts/generar_esquema_base.py. Para rehacerlo, aplica antes la",
        "-- migracion nueva a ese schema y vuelve a ejecutar el script.",
        "--",
        "-- Se aplica con el search_path apuntando SOLO al schema destino. Sus",
        "-- nombres no van cualificados: con otro schema en el camino, las claves",
        "-- foraneas naceran apuntando alli.",
        "--",
        "-- No usar apply_migration.py con este archivo: es para dar de alta un",
        "-- tenant nuevo, no para los existentes, que ya tienen estas tablas.",
        "--",
        f"-- MIGRACIONES INCORPORADAS ({len(incorporadas)}):",
    ]
    lineas.extend(f"--   {nombre}" for nombre in incorporadas)
    lineas.append("-- FIN MIGRACIONES INCORPORADAS")
    return lineas


def generar(cursor, schema, generado_el):
    cursor.execute("SET TRANSACTION READ ONLY")
    # Con el search_path en el schema, pg_get_constraintdef y pg_get_functiondef
    # omiten el prefijo y el SQL sale portable. pg_get_indexdef es la excepcion:
    # cualifica siempre la tabla y hay que quitarselo.
    cursor.execute(f'SET LOCAL search_path TO "{schema}"')

    lista = tablas(cursor, schema)
    lineas = cabecera(schema, migraciones_incorporadas(cursor, schema), generado_el)
    lineas.append("")

    for tabla in lista:
        cuerpo = [definicion_columna(*col) for col in columnas(cursor, schema, tabla)]
        for nombre, definicion in restricciones(cursor, schema, tabla, ("p", "u", "c")):
            cuerpo.append(f"    CONSTRAINT {nombre} {definicion}")
        lineas.append(f"CREATE TABLE IF NOT EXISTS {tabla} (")
        lineas.append(",\n".join(cuerpo))
        lineas.append(");")
        lineas.append("")

    lineas.append("-- Indices que no respaldan restricciones")
    for tabla in lista:
        for definicion in indices_sueltos(cursor, schema, tabla):
            portable = definicion.replace(f"{schema}.", "")
            lineas.append(
                portable.replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS ")
                .replace("CREATE UNIQUE INDEX ", "CREATE UNIQUE INDEX IF NOT EXISTS ")
                + ";"
            )
    lineas.append("")

    lineas.append("-- Claves foraneas, al final para no depender del orden de creacion")
    for tabla in lista:
        for nombre, definicion in restricciones(cursor, schema, tabla, ("f",)):
            lineas.append(f"ALTER TABLE {tabla} ADD CONSTRAINT {nombre} {definicion};")
    lineas.append("")

    fns = funciones(cursor, schema)
    if fns:
        lineas.append("-- Funciones")
        for definicion in fns:
            lineas.append(definicion.replace(f"{schema}.", "") + ";")
        lineas.append("")

    trg = disparadores(cursor, schema)
    if trg:
        lineas.append("-- Disparadores")
        for definicion in trg:
            lineas.append(definicion.replace(f"{schema}.", "") + ";")
        lineas.append("")

    return "\n".join(lineas), len(lista), len(fns), len(trg)


def main(schema: str, salida: Path) -> int:
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("X DATABASE_URL no esta definido en .env")
        return 1

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cursor = conn.cursor()
    try:
        contenido, n_tablas, n_fns, n_trg = generar(
            cursor, schema, date.today().isoformat()
        )
        if not n_tablas:
            print(f"X El schema {schema} no tiene tablas. No se escribio nada.")
            return 2

        # Una sola linea nueva al final: mas dejaria un blanco que git marca.
        contenido = contenido.rstrip("\n") + "\n"
        salida.parent.mkdir(parents=True, exist_ok=True)
        previo = salida.read_text(encoding="utf-8") if salida.exists() else ""
        salida.write_text(contenido, encoding="utf-8")

        print(f"escrito: {salida}")
        print(f"  tablas {n_tablas}, funciones {n_fns}, disparadores {n_trg}")
        print(f"  {'sin cambios respecto al anterior' if previo == contenido else 'el contenido CAMBIO'}")
        return 0
    finally:
        conn.rollback()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Regenera la migracion base a partir de un schema real."
    )
    parser.add_argument(
        "--schema",
        default=os.getenv("DEFAULT_TENANT_SCHEMA", "tenant_colegio_1"),
        help="Schema del que se extrae la estructura",
    )
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO)
    args = parser.parse_args()
    raise SystemExit(main(args.schema, args.salida))
