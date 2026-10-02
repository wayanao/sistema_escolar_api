from app.database import get_connection, get_cursor
from app.repositories import planeador_anual_repository
from app.schemas.planeador_anual import PlaneadorAnualCreate, PlaneadorAnualUpdate
from app.services.anio_lectivo import exigir_asignacion_editable
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor
from typing import List

def crear_planeador_anual_controller(planeador: PlaneadorAnualCreate):
    with get_cursor(commit=True) as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, planeador.asignacion_id)
        planeador_anual_repository.insertar_planeador_anual(
            cursor,
            asignacion_id,
            planeador.periodo,
            planeador.slot,
            planeador.unidad_tematica,
            planeador.estandar_competencia,
            planeador.contenido,
            planeador.actividades_recursos,
            planeador.fecha,
        )
        planeador_id = cursor.fetchone()[0]

    return planeador_id

def obtener_planeadores_anual_controller(asignacion_id: int, periodo: int) -> List[dict]:
    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        planeador_anual_repository.seleccionar_planeadores_anuales(
            cursor,
            asignacion_id,
            periodo,
        )
        rows = cursor.fetchall()

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
    with get_cursor(commit=True) as cursor:
        planeador_anual_repository.actualizar_planeador_anual(
            cursor,
            planeador_id,
            planeador.unidad_tematica,
            planeador.estandar_competencia,
            planeador.contenido,
            planeador.actividades_recursos,
            planeador.fecha,
        )

def bulk_actualizar_planeadores_controller(
    asignacion_id: int,
    periodo: int,
    planeadores: List[PlaneadorAnualUpdate],
    *,
    usuario,
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_asignacion_editable(cursor, asignacion_id, usuario)
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
                planeador_anual_repository.eliminar_slot_planeador(
                    cursor,
                    asignacion_id,
                    periodo,
                    slot,
                )
                continue

            planeador_anual_repository.guardar_slot_planeador(
                cursor,
                asignacion_id,
                periodo,
                slot,
                planeador.unidad_tematica,
                planeador.estandar_competencia,
                planeador.contenido,
                planeador.actividades_recursos,
                planeador.fecha,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
