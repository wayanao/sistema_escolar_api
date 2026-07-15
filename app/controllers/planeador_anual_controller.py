from app.database import get_connection
from app.schemas.planeador_anual import PlaneadorAnualCreate, PlaneadorAnualUpdate
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor
from typing import List

def crear_planeador_anual_controller(planeador: PlaneadorAnualCreate):
    conn = get_connection()
    cursor = conn.cursor()
    asignacion_id = resolver_asignacion_academica_id_cursor(cursor, planeador.asignacion_id)
    cursor.execute("""
        INSERT INTO planeador_anual (asignacion_id, periodo, slot, unidad_tematica, estandar_competencia, contenido, actividades_recursos, fecha)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        asignacion_id,
        planeador.periodo,
        planeador.slot,
        planeador.unidad_tematica,
        planeador.estandar_competencia,
        planeador.contenido,
        planeador.actividades_recursos,
        planeador.fecha
    ))
    planeador_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return planeador_id

def obtener_planeadores_anual_controller(asignacion_id: int, periodo: int) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
    cursor.execute("""
        SELECT id, asignacion_id, periodo, slot, unidad_tematica, estandar_competencia, contenido, actividades_recursos, fecha
        FROM planeador_anual
        WHERE asignacion_id = %s AND periodo = %s
        ORDER BY slot
    """, (asignacion_id, periodo))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {
            "id": row[0],
            "asignacion_id": row[1],
            "periodo": row[2],
            "slot": row[3],
            "unidad_tematica": row[4],
            "estandar_competencia": row[5],
            "contenido": row[6],
            "actividades_recursos": row[7],
            "fecha": row[8]
        }
        for row in rows
    ]

def actualizar_planeador_anual_controller(planeador_id: int, planeador: PlaneadorAnualUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE planeador_anual
        SET unidad_tematica = %s, estandar_competencia = %s, contenido = %s, actividades_recursos = %s, fecha = %s
        WHERE id = %s
    """, (
        planeador.unidad_tematica,
        planeador.estandar_competencia,
        planeador.contenido,
        planeador.actividades_recursos,
        planeador.fecha,
        planeador_id
    ))
    conn.commit()
    cursor.close()
    conn.close()

def bulk_actualizar_planeadores_controller(asignacion_id: int, periodo: int, planeadores: List[PlaneadorAnualUpdate]):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        for i, planeador in enumerate(planeadores):
            slot = i + 1
            tiene_contenido = any((
                planeador.unidad_tematica,
                planeador.estandar_competencia,
                planeador.contenido,
                planeador.actividades_recursos,
            ))

            if not tiene_contenido:
                cursor.execute("""
                    DELETE FROM planeador_anual
                    WHERE asignacion_id = %s AND periodo = %s AND slot = %s
                """, (asignacion_id, periodo, slot))
                continue

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
                planeador.unidad_tematica,
                planeador.estandar_competencia,
                planeador.contenido,
                planeador.actividades_recursos,
                planeador.fecha,
            ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
