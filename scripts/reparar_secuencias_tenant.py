"""Da secuencias propias a un tenant que esta usando las de otro schema.

Uso:
    python scripts/reparar_secuencias_tenant.py --schema tenant_2005 --dry-run
    python scripts/reparar_secuencias_tenant.py --schema tenant_2005

El alta de tenants copiaba la estructura con LIKE INCLUDING ALL, que conserva el
DEFAULT original: las columnas quedaron generando su id con nextval de las
secuencias del schema plantilla. Este script crea una secuencia propia por
columna afectada, la posiciona en el MAX(id) real medido en ese momento y
reapunta el DEFAULT.

Es de un solo uso por tenant, idempotente y auto-verificable. Mide siempre
contra la base en la que corre: no lleva ningun valor precalculado.

Todo ocurre en una sola transaccion y es reversible: las secuencias se
posicionan con ALTER SEQUENCE ... RESTART, que si se revierte con el rollback,
en lugar de setval(), que no. Si la verificacion final falla, no se confirma
nada y la base queda como estaba.
"""
import argparse
import os
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]


def detectar_columnas_prestadas(cursor, schema: str):
    """Columnas cuyo DEFAULT usa una secuencia que vive en OTRO schema."""
    cursor.execute(
        """
        SELECT c.relname, a.attname, pg_get_expr(d.adbin, d.adrelid), t.typname
        FROM pg_attrdef d
        JOIN pg_class c ON c.oid = d.adrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
        JOIN pg_type t ON t.oid = a.atttypid
        WHERE n.nspname = %s
        ORDER BY c.relname, a.attname
        """,
        (schema,),
    )
    prestadas = []
    for tabla, columna, expresion, tipo in cursor.fetchall():
        if "nextval(" not in expresion:
            continue
        referencia = expresion.split("'")[1]
        if "." not in referencia:
            continue
        schema_origen = referencia.split(".", 1)[0].strip('"')
        if schema_origen == schema:
            continue
        prestadas.append(
            {
                "tabla": tabla,
                "columna": columna,
                "default_original": expresion,
                "schema_origen": schema_origen,
                "tipo": tipo,
            }
        )
    return prestadas


def nombre_secuencia_propia(tabla: str, columna: str) -> str:
    return f"{tabla}_{columna}_seq"


def tipo_de_secuencia(tipo_columna: str) -> str:
    return "bigint" if tipo_columna == "int8" else "integer"


def maximo_actual(cursor, schema: str, tabla: str, columna: str) -> int:
    cursor.execute(
        sql.SQL("SELECT COALESCE(MAX({}), 0) FROM {}.{}").format(
            sql.Identifier(columna), sql.Identifier(schema), sql.Identifier(tabla)
        )
    )
    return cursor.fetchone()[0]


def construir_plan(cursor, schema: str):
    """Une cada columna prestada con el maximo medido y su secuencia destino."""
    plan = []
    for prestada in detectar_columnas_prestadas(cursor, schema):
        maximo = maximo_actual(cursor, schema, prestada["tabla"], prestada["columna"])
        plan.append(
            {
                **prestada,
                "maximo": maximo,
                "secuencia": nombre_secuencia_propia(
                    prestada["tabla"], prestada["columna"]
                ),
            }
        )
    return plan


def reparar_columna(cursor, schema: str, paso: dict) -> None:
    secuencia = sql.Identifier(schema, paso["secuencia"])
    tabla = sql.Identifier(schema, paso["tabla"])
    columna = sql.Identifier(paso["columna"])

    cursor.execute(
        sql.SQL("CREATE SEQUENCE IF NOT EXISTS {} AS {}").format(
            secuencia, sql.SQL(tipo_de_secuencia(paso["tipo"]))
        )
    )
    # Se posiciona con ALTER SEQUENCE ... RESTART y NO con setval(): setval no es
    # transaccional y su efecto sobrevive a un rollback, mientras que RESTART si
    # se revierte. Comprobado contra PostgreSQL 17: dentro de una transaccion
    # revertida, el valor puesto por setval persistio y el puesto por RESTART
    # volvio atras. Usar setval aqui haria que un fallo dejase las secuencias
    # movidas aunque no se confirmara nada.
    # RESTART WITH n deja el siguiente nextval en n, asi que con la tabla vacia
    # (maximo 0) el siguiente es 1, que es justo lo que se quiere.
    cursor.execute(
        sql.SQL("ALTER SEQUENCE {} RESTART WITH {}").format(
            secuencia, sql.Literal(paso["maximo"] + 1)
        )
    )
    cursor.execute(
        sql.SQL("ALTER TABLE {} ALTER COLUMN {} SET DEFAULT nextval({}::regclass)").format(
            tabla, columna, sql.Literal(f'{schema}.{paso["secuencia"]}')
        )
    )
    cursor.execute(
        sql.SQL("ALTER SEQUENCE {} OWNED BY {}.{}").format(secuencia, tabla, columna)
    )


def verificar(cursor, schema: str):
    """Devuelve los problemas que queden; vacia significa reparacion correcta."""
    problemas = []
    for prestada in detectar_columnas_prestadas(cursor, schema):
        problemas.append(
            f'{prestada["tabla"]}.{prestada["columna"]} sigue usando '
            f'{prestada["schema_origen"]}'
        )

    cursor.execute(
        """
        SELECT c.relname, a.attname, pg_get_expr(d.adbin, d.adrelid)
        FROM pg_attrdef d
        JOIN pg_class c ON c.oid = d.adrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
        WHERE n.nspname = %s
        """,
        (schema,),
    )
    columnas = [
        (tabla, columna, expresion.split("'")[1])
        for tabla, columna, expresion in cursor.fetchall()
        if "nextval(" in expresion
    ]
    for tabla, columna, referencia in columnas:
        partes = referencia.replace('"', "").split(".", 1)
        cursor.execute(
            sql.SQL("SELECT last_value, is_called FROM {}").format(
                sql.Identifier(*partes)
            )
        )
        last_value, is_called = cursor.fetchone()
        siguiente = last_value + 1 if is_called else last_value
        maximo = maximo_actual(cursor, schema, tabla, columna)
        if siguiente <= maximo:
            problemas.append(
                f"{tabla}.{columna}: siguiente id {siguiente} <= maximo {maximo}"
            )
    return problemas


def main(schema: str, dry_run: bool = False) -> int:
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("X DATABASE_URL no esta definido en .env")
        return 1

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        plan = construir_plan(cursor, schema)
        if not plan:
            print(f"Nada que reparar: {schema} no usa secuencias de otro schema.")
            conn.rollback()
            return 0

        print(f"\n>> {schema}: {len(plan)} columna(s) usando secuencias ajenas\n")
        for paso in plan:
            print(
                f'  {paso["tabla"]}.{paso["columna"]}: '
                f'{paso["schema_origen"]} -> {schema}.{paso["secuencia"]} '
                f'(maximo actual {paso["maximo"]})'
            )
            print(f'      DEFAULT anterior: {paso["default_original"]}')

        if dry_run:
            print("\n>> Simulacion: no se aplico ningun cambio.")
            conn.rollback()
            return 0

        for paso in plan:
            reparar_columna(cursor, schema, paso)

        problemas = verificar(cursor, schema)
        if problemas:
            conn.rollback()
            print("\n!! Verificacion fallida, no se confirmo nada:")
            for problema in problemas:
                print(f"  - {problema}")
            return 2

        conn.commit()
        print(f"\n>> Reparadas {len(plan)} columna(s). Verificacion correcta.")
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
        description="Da secuencias propias a un tenant que usa las de otro schema."
    )
    parser.add_argument("--schema", required=True, help="Schema del tenant a reparar")
    parser.add_argument(
        "--dry-run", action="store_true", help="Muestra el plan sin aplicarlo"
    )
    args = parser.parse_args()
    raise SystemExit(main(args.schema, dry_run=args.dry_run))
