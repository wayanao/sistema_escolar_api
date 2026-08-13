"""Registra en public.schema_migrations lo que un tenant ya tiene aplicado.

Uso:
    python scripts/sembrar_historial_tenant.py --schema tenant_2005 --dry-run
    python scripts/sembrar_historial_tenant.py --schema tenant_2005

Un tenant creado copiando el schema plantilla hereda su estructura pero nace con
historial vacio, asi que el runner lo ve como si le faltaran migraciones que en
realidad ya estan. Este script copia los registros de la plantilla para las que
falten.

No es un acto de fe: antes de sembrar comprueba que el schema destino es
estructuralmente equivalente a la plantilla en columnas e indices, y se niega si
no lo es. Las claves foraneas se excluyen de esa comparacion a proposito: su
ausencia proviene de la copia con LIKE INCLUDING ALL, que no las reproduce, y no
de una migracion sin aplicar.

Todo ocurre en una transaccion y no aplica ninguna migracion: solo escribe
historial.
"""
import argparse
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]


def columnas(cursor, schema):
    cursor.execute(
        """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s
        """,
        (schema,),
    )
    return {(t, c): (d, n) for t, c, d, n in cursor.fetchall()}


def indices(cursor, schema):
    """Indices por su FUNCION: tabla, unicidad, columnas y condicion.

    El nombre se descarta a proposito. La plantilla y los tenants siguen
    convenciones distintas —`idx_cursos_estado` frente a `cursos_estado_idx`—
    y comparar nombres daria diferencias que no significan nada: lo que una
    migracion aporta es el indice, no como se llama.
    """
    cursor.execute(
        "SELECT tablename, indexdef FROM pg_indexes WHERE schemaname = %s",
        (schema,),
    )
    resultado = set()
    for tabla, definicion in cursor.fetchall():
        cuerpo = definicion.split(" ON ", 1)[1].replace(f"{schema}.", "")
        unico = definicion.startswith("CREATE UNIQUE")
        resultado.add((tabla, unico, " ".join(cuerpo.split())))
    return resultado


def diferencias_estructurales(cursor, plantilla, destino):
    """Columnas e indices que el destino no reproduce. Ignora claves foraneas."""
    base_col, destino_col = columnas(cursor, plantilla), columnas(cursor, destino)
    base_idx, destino_idx = indices(cursor, plantilla), indices(cursor, destino)

    problemas = []
    for clave in sorted(set(base_col) - set(destino_col)):
        problemas.append(f"falta la columna {clave[0]}.{clave[1]}")
    for clave in sorted(set(base_col) & set(destino_col)):
        if base_col[clave] != destino_col[clave]:
            problemas.append(
                f"{clave[0]}.{clave[1]} difiere: plantilla={base_col[clave]} "
                f"destino={destino_col[clave]}"
            )
    # Solo importa que al destino no le falte nada. Que tenga indices de mas no
    # es evidencia de una migracion sin aplicar.
    for tabla, unico, cuerpo in sorted(base_idx - destino_idx):
        etiqueta = "indice unico" if unico else "indice"
        problemas.append(f"falta un {etiqueta} en {tabla}: {cuerpo[:70]}")
    return problemas


def migraciones_por_sembrar(cursor, plantilla, destino):
    cursor.execute(
        """
        SELECT migration_name, checksum
        FROM public.schema_migrations
        WHERE target_schema = %s
          AND migration_name NOT IN (
              SELECT migration_name FROM public.schema_migrations
              WHERE target_schema = %s
          )
        ORDER BY migration_name
        """,
        (plantilla, destino),
    )
    return cursor.fetchall()


def sembrar(cursor, plantilla, destino) -> int:
    cursor.execute(
        """
        INSERT INTO public.schema_migrations (migration_name, target_schema, checksum)
        SELECT migration_name, %s, checksum
        FROM public.schema_migrations origen
        WHERE origen.target_schema = %s
          AND NOT EXISTS (
              SELECT 1 FROM public.schema_migrations ya
              WHERE ya.target_schema = %s
                AND ya.migration_name = origen.migration_name
          )
        """,
        (destino, plantilla, destino),
    )
    return cursor.rowcount


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
        pendientes = migraciones_por_sembrar(cursor, plantilla, schema)
        if not pendientes:
            print(f"Nada que sembrar: {schema} ya registra todo lo de {plantilla}.")
            conn.rollback()
            return 0

        print(f"\n>> {schema}: {len(pendientes)} migracion(es) sin registrar\n")
        for nombre, _ in pendientes:
            print(f"  {nombre}")

        problemas = diferencias_estructurales(cursor, plantilla, schema)
        print(f"\n>> Comprobacion estructural frente a {plantilla}: "
              f"{'sin diferencias' if not problemas else str(len(problemas)) + ' diferencia(s)'}")
        for problema in problemas[:10]:
            print(f"  - {problema}")
        if problemas:
            print("\n!! El destino no reproduce la estructura de la plantilla.")
            print("   Sembrar el historial afirmaria algo falso. No se hizo nada.")
            conn.rollback()
            return 2

        if dry_run:
            print("\n>> Simulacion: no se registro nada.")
            conn.rollback()
            return 0

        insertadas = sembrar(cursor, plantilla, schema)
        restantes = migraciones_por_sembrar(cursor, plantilla, schema)
        if restantes:
            conn.rollback()
            print(f"\n!! Quedaron {len(restantes)} sin sembrar. Se revirtio todo.")
            return 2

        conn.commit()
        print(f"\n>> Registradas {insertadas} migracion(es) para {schema}.")
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
        description="Registra en el historial lo que un tenant ya tiene aplicado."
    )
    parser.add_argument("--schema", required=True, help="Schema del tenant")
    parser.add_argument(
        "--plantilla",
        default=os.getenv("DEFAULT_TENANT_SCHEMA", "tenant_colegio_1"),
        help="Schema de referencia del que se copian los registros",
    )
    parser.add_argument("--dry-run", action="store_true", help="Muestra sin escribir")
    args = parser.parse_args()
    raise SystemExit(main(args.schema, args.plantilla, dry_run=args.dry_run))
