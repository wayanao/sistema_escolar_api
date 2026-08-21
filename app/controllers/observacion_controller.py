from app.database import get_connection
from app.repositories import observaciones_repository
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor



def guardar_observacion_controller(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, data["asignacion_id"])

        observaciones_repository.guardar_observacion(
            cursor,
            data["estudiante_id"],
            asignacion_id,
            data["periodo"],
            data.get("conductual", ""),
            data.get("cognitivo", ""),
            data.get("lenguaje", ""),
        )

        conn.commit()
        return {"mensaje": "Observación guardada/actualizada"}
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
