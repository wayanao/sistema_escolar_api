from app.database import get_connection
from app.repositories import observaciones_repository
from app.services.anio_lectivo import exigir_asignacion_editable
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor


class AsignacionInactivaError(Exception):
    """La asignacion existe pero esta dada de baja.

    Se distingue de un fallo de infraestructura porque la ruta la traduce a
    **403**, no a 500. Es la razon de que exista esta clase: sin ella el rechazo
    caeria en el `except Exception` y saldria como error del servidor.
    """


def guardar_observacion_controller(data, *, usuario):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_asignacion_editable(cursor, data["asignacion_id"], usuario)
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, data["asignacion_id"])

        if not observaciones_repository.asignacion_esta_activa(cursor, asignacion_id):
            raise AsignacionInactivaError(asignacion_id)

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
