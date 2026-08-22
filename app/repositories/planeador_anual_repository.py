"""Persistencia propia del dominio de planeador anual."""


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
