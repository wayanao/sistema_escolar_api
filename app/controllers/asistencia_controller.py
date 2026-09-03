from app.core.nivel_academico import (
    MENSAJE_ASISTENCIA_REQUIERE_JORNADA,
    asistencia_rechazada_por_nivel,
)
from app.database import get_connection, get_cursor
from app.repositories.asistencia_repository import (
    borrar_asistencia_del_lote,
    insertar_asistencia,
    leer_historial_de_asignacion,
)
from app.services.asignacion_academica import (
    resolver_asignacion_academica_id_cursor,
    resolver_nivel_y_materia_cursor,
)

def guardar_asistencia_controller(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, data[0].asignacion_id)

        nivel, nombre_materia = resolver_nivel_y_materia_cursor(cursor, asignacion_id)
        if asistencia_rechazada_por_nivel(nivel, nombre_materia):
            return {"error": MENSAJE_ASISTENCIA_REQUIERE_JORNADA}

        borrar_asistencia_del_lote(
            cursor,
            asignacion_id,
            data[0].fecha,
            data[0].periodo,
            [item.estudiante_id for item in data],
        )

        for item in data:
            insertar_asistencia(
                cursor,
                item.estudiante_id,
                asignacion_id,
                item.fecha,
                item.estado,
                item.periodo,
            )

        conn.commit()
        return {"mensaje": "Asistencia guardada"}
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def obtener_historial_asistencia(asignacion_id, periodo=1):

    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

        rows = leer_historial_de_asignacion(cursor, asignacion_id, periodo)

    resultado = {}

    for r in rows:
        est_id = r[0]

        if est_id not in resultado:
            resultado[est_id] = {
                "estudiante_id": est_id,
                "nombre": r[1],
                "apellido": r[2],
                "historial": []
            }

        # fecha está en r[3], estado en r[4]
        if r[3]:
            resultado[est_id]["historial"].append({
                "fecha": str(r[3]),
                "estado": r[4]
            })

    return list(resultado.values())
