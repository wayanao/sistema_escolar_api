"""Persistencia propia del dominio de planeador anual.

Año lectivo, fase 7: leer si se puede traer el planeador del año pasado a una
clase, y traerlo. Ver docs/funcionalidades/ANIO_LECTIVO.md.
"""
from app.repositories.anios_lectivos_repository import CLASES_DE_ORIGEN_SQL

# Una fila "escrita": con algún texto en alguno de sus cuatro campos. `{t}` es
# el alias de la tabla, escrito en el código.
_CON_TEXTO = (
    "(TRIM(COALESCE({t}.unidad_tematica, '')) <> ''"
    " OR TRIM(COALESCE({t}.estandar_competencia, '')) <> ''"
    " OR TRIM(COALESCE({t}.contenido, '')) <> ''"
    " OR TRIM(COALESCE({t}.actividades_recursos, '')) <> '')"
)
_ORIGEN_CON_TEXTO = _CON_TEXTO.format(t="o")
_FILA_CON_TEXTO = _CON_TEXTO.format(t="p")

# Fase 7: las filas del año pasado que se traen a una clase (decisión 14). Para
# cada periodo, las de la clase de origen más reciente (la de id mayor) que
# escribió algo en ese periodo: si la materia cambió de profesor a mitad de
# año, cada periodo sale entero del último que lo llenó (decisión del usuario,
# 2026-10-10). Un `%s`: el id de la clase de este año.
_FILAS_DEL_ANIO_ANTERIOR = f"""
    FROM planeador_anual p
    WHERE (p.asignacion_id, p.periodo) IN (
        SELECT MAX(o.asignacion_id), o.periodo
        FROM planeador_anual o
        WHERE o.asignacion_id IN ({CLASES_DE_ORIGEN_SQL})
          AND {_ORIGEN_CON_TEXTO}
        GROUP BY o.periodo
    )
      AND {_FILA_CON_TEXTO}
"""


def insertar_planeador_anual(
    cursor,
    asignacion_id,
    periodo,
    slot,
    unidad_tematica,
    estandar_competencia,
    contenido,
    actividades_recursos,
    fecha,
):
    cursor.execute("""
            INSERT INTO planeador_anual (asignacion_id, periodo, slot, unidad_tematica, estandar_competencia, contenido, actividades_recursos, fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            asignacion_id,
            periodo,
            slot,
            unidad_tematica,
            estandar_competencia,
            contenido,
            actividades_recursos,
            fecha
        ))


def seleccionar_planeadores_anuales(cursor, asignacion_id, periodo):
    cursor.execute("""
            SELECT id, asignacion_id, periodo, slot, unidad_tematica, estandar_competencia, contenido, actividades_recursos, fecha
            FROM planeador_anual
            WHERE asignacion_id = %s AND periodo = %s
            ORDER BY slot
        """, (asignacion_id, periodo))


def actualizar_planeador_anual(
    cursor,
    planeador_id,
    unidad_tematica,
    estandar_competencia,
    contenido,
    actividades_recursos,
    fecha,
):
    cursor.execute("""
            UPDATE planeador_anual
            SET unidad_tematica = %s, estandar_competencia = %s, contenido = %s, actividades_recursos = %s, fecha = %s
            WHERE id = %s
        """, (
            unidad_tematica,
            estandar_competencia,
            contenido,
            actividades_recursos,
            fecha,
            planeador_id
        ))


def eliminar_slot_planeador(cursor, asignacion_id, periodo, slot):
    cursor.execute("""
                    DELETE FROM planeador_anual
                    WHERE asignacion_id = %s AND periodo = %s AND slot = %s
                """, (asignacion_id, periodo, slot))


def guardar_slot_planeador(
    cursor,
    asignacion_id,
    periodo,
    slot,
    unidad_tematica,
    estandar_competencia,
    contenido,
    actividades_recursos,
    fecha,
):
    cursor.execute("""
                INSERT INTO planeador_anual (asignacion_id, periodo, slot, unidad_tematica, estandar_competencia, contenido, actividades_recursos, fecha)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (asignacion_id, periodo, slot) DO UPDATE SET
                    unidad_tematica = EXCLUDED.unidad_tematica,
                    estandar_competencia = EXCLUDED.estandar_competencia,
                    contenido = EXCLUDED.contenido,
                    actividades_recursos = EXCLUDED.actividades_recursos,
                    fecha = EXCLUDED.fecha
            """, (
                asignacion_id,
                periodo,
                slot,
                unidad_tematica,
                estandar_competencia,
                contenido,
                actividades_recursos,
                fecha,
            ))


def leer_planeador_anio_anterior(cursor, asignacion_id, destino_id):
    """Lo que decide si se puede traer el planeador del año pasado a una clase.

    Una consulta. Devuelve `(anio, estado, tiene_filas, hay_origen)`: el año
    de la clase y su estado (para la guardia), si su planeador ya tiene alguna
    fila y si hay algo escrito que traer; o `None` si la clase no existe.
    `asignacion_id` es la clase que se pidió; `destino_id`, la clase académica
    ya resuelta, que es la que guarda el planeador.
    """
    cursor.execute(
        f"""
        SELECT al.anio, al.estado,
               EXISTS (SELECT 1 FROM planeador_anual d WHERE d.asignacion_id = %s),
               EXISTS (SELECT 1 {_FILAS_DEL_ANIO_ANTERIOR})
        FROM asignaciones a
        JOIN cursos c ON c.id = a.curso_id
        JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
        WHERE a.id = %s
        """,
        (destino_id, asignacion_id, asignacion_id),
    )
    return cursor.fetchone()


def copiar_planeador_anio_anterior(cursor, asignacion_id, destino_id):
    """Copia a la clase el planeador del año pasado y devuelve cuántas filas.

    Una sola sentencia (`INSERT ... SELECT`): las filas no pasan por Python.
    Copia periodo, slot y los cuatro textos; la fecha queda vacía, porque las
    de un año no sirven en el otro (fase 7, punto 2). No mira si la clase ya
    tiene filas: eso lo decide quien llama, antes; si otra petición escribió
    entre tanto, la regla única (clase, periodo, slot) hace fallar el INSERT.
    """
    cursor.execute(
        f"""
        INSERT INTO planeador_anual (asignacion_id, periodo, slot, unidad_tematica, estandar_competencia, contenido, actividades_recursos, fecha)
        SELECT %s, p.periodo, p.slot, p.unidad_tematica, p.estandar_competencia, p.contenido, p.actividades_recursos, NULL
        {_FILAS_DEL_ANIO_ANTERIOR}
        """,
        (destino_id, asignacion_id),
    )
    return cursor.rowcount
