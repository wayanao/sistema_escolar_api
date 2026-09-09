"""Copia las observaciones viejas a la bitacora nueva del observador.

    python scripts/copiar_observaciones_al_observador.py --dry-run
    python scripts/copiar_observaciones_al_observador.py

Fase 4 de `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. La tabla vieja
`observaciones` **no se toca ni se borra**: esto solo lee de ella.

**Repetible sin duplicar.** Cada anotacion copiada guarda de que fila salio, en
`observacion_origen_id`, que ademas es UNIQUE. Ejecutarlo dos veces no crea
nada nuevo. Era el riesgo que el documento ya tenia anotado.

Lo que se recupera de cada fila vieja:

* el **profesor** y la **materia**, a traves de su `asignacion_id`;
* el **periodo** y los tres textos, tal cual.

Lo que **no** se puede recuperar, porque no existe en el modelo viejo:

* la **fecha**: `observaciones` nunca la guardo. Va `NULL`, que significa «no se
  sabe», y la lectura las manda al final con `NULLS LAST`. Inventar la fecha de
  la copia las haria parecer escritas hoy;
* si era **positiva o negativa**: el modelo viejo no distinguia. Va `NULL`,
  «sin marcar». Decidido con el usuario: no se les inventa una marca.

El texto se copia **tal cual**, sin pasarlo por la correccion de mayusculas. Lo
que escribio una profesora hace meses es historico: no se reescribe.

Este script NO usa el runner de migraciones porque mueve datos, no estructura.
Trabaja tenant por tenant, con una transaccion por tenant.
"""
import argparse
import os

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


load_dotenv()

# Solo se copia lo que la tabla nueva admite. Lo que no pasa el filtro se
# cuenta y se informa: 68 no pueden convertirse en 60 en silencio.
_CONDICIONES_COPIABLE = """
        o.estudiante_id IS NOT NULL
    AND a.profesor_id IS NOT NULL
    AND o.periodo BETWEEN 1 AND 4
    AND (
            COALESCE(TRIM(o.conductual), '') <> ''
         OR COALESCE(TRIM(o.cognitivo), '') <> ''
         OR COALESCE(TRIM(o.lenguaje), '') <> ''
        )
"""

_INSERT = f"""
INSERT INTO observador_anotaciones (
    estudiante_id, profesor_id, periodo, positiva,
    conductual, cognitivo, lenguaje,
    materia, creada_en, observacion_origen_id
)
SELECT o.estudiante_id,
       a.profesor_id,
       o.periodo,
       NULL,
       COALESCE(o.conductual, ''),
       COALESCE(o.cognitivo, ''),
       COALESCE(o.lenguaje, ''),
       COALESCE(m.nombre, ''),
       NULL,
       o.id
  FROM observaciones o
  JOIN asignaciones a ON a.id = o.asignacion_id
  LEFT JOIN materias m ON m.id = a.materia_id
 WHERE {_CONDICIONES_COPIABLE}
ON CONFLICT (observacion_origen_id) DO NOTHING
"""

_RECUENTO = f"""
SELECT count(*) AS total,
       count(*) FILTER (WHERE {_CONDICIONES_COPIABLE}) AS copiables,
       count(*) FILTER (WHERE o.estudiante_id IS NULL) AS sin_estudiante,
       count(*) FILTER (WHERE o.asignacion_id IS NULL OR a.id IS NULL
                           OR a.profesor_id IS NULL) AS sin_profesor,
       count(*) FILTER (WHERE o.periodo IS NULL
                           OR o.periodo NOT BETWEEN 1 AND 4) AS periodo_invalido,
       count(*) FILTER (WHERE COALESCE(TRIM(o.conductual), '') = ''
                          AND COALESCE(TRIM(o.cognitivo), '') = ''
                          AND COALESCE(TRIM(o.lenguaje), '') = '') AS sin_texto
  FROM observaciones o
  LEFT JOIN asignaciones a ON a.id = o.asignacion_id
"""

_YA_COPIADAS = "SELECT count(*) FROM observador_anotaciones WHERE observacion_origen_id IS NOT NULL"


def tenants(cursor):
    cursor.execute("""
        SELECT esquema_db
        FROM public.colegios
        WHERE LOWER(estado) IN ('activo', 'en_mora')
        ORDER BY esquema_db
    """)
    return [fila[0] for fila in cursor.fetchall()]


def tabla_existe(cursor, esquema, tabla):
    cursor.execute("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
    """, (esquema, tabla))
    return cursor.fetchone() is not None


def copiar(dry_run=False):
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no esta configurado")

    conn = psycopg2.connect(url)
    conn.autocommit = False
    total_copiadas = 0
    try:
        cursor = conn.cursor()
        esquemas = tenants(cursor)
        conn.rollback()

        modo = "SIMULANDO" if dry_run else "COPIANDO"
        print(f"\n>> {modo} en {len(esquemas)} tenant(s)\n")

        for esquema in esquemas:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    sql.SQL("SET search_path TO {}, public").format(sql.Identifier(esquema))
                )

                if not tabla_existe(cursor, esquema, "observador_anotaciones"):
                    print(f"  {esquema}: falta la tabla nueva, omitido. "
                          "Aplica antes las migraciones del observador.")
                    conn.rollback()
                    continue

                cursor.execute(_YA_COPIADAS)
                ya = cursor.fetchone()[0]

                cursor.execute(_RECUENTO)
                total, copiables, sin_est, sin_prof, periodo_malo, sin_texto = cursor.fetchone()

                print(f"  {esquema}")
                print(f"     observaciones viejas ....... {total}")
                print(f"     ya copiadas antes .......... {ya}")
                print(f"     copiables .................. {copiables}")

                descartes = [
                    ("sin estudiante", sin_est),
                    ("sin profesor o asignacion", sin_prof),
                    ("periodo fuera de 1-4", periodo_malo),
                    ("las tres dimensiones vacias", sin_texto),
                ]
                for motivo, cuantas in descartes:
                    if cuantas:
                        print(f"     NO se copian, {motivo}: {cuantas}")

                if dry_run:
                    print(f"     -> se insertarian {max(copiables - ya, 0)}")
                    conn.rollback()
                    continue

                cursor.execute(_INSERT)
                insertadas = cursor.rowcount
                conn.commit()
                total_copiadas += insertadas
                print(f"     -> insertadas {insertadas}")
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                print(f"     !! FALLO en {esquema}: {type(exc).__name__}: {exc}")
                raise
            finally:
                cursor.close()

        if dry_run:
            print("\n>> Simulacion completada. No se copio nada.")
        else:
            print(f"\n>> Copiadas {total_copiadas} anotaciones. "
                  "La tabla `observaciones` no se ha tocado.")
    finally:
        conn.close()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Copia las observaciones viejas a la bitacora del observador."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Cuenta que se copiaria, sin escribir nada",
    )
    args = parser.parse_args()
    return copiar(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
