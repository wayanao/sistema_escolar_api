from app.database import get_connection
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor



def guardar_observacion_controller(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, data["asignacion_id"])

        cursor.execute("""
            INSERT INTO observaciones (
                estudiante_id,
                asignacion_id,
                periodo,
                conductual,
                cognitivo,
                lenguaje
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (estudiante_id, asignacion_id, periodo)
            DO UPDATE SET
                conductual = EXCLUDED.conductual,
                cognitivo = EXCLUDED.cognitivo,
                lenguaje = EXCLUDED.lenguaje
        """, (
            data["estudiante_id"],
            asignacion_id,
            data["periodo"],
            data.get("conductual", ""),
            data.get("cognitivo", ""),
            data.get("lenguaje", ""),
        ))

        conn.commit()
        return {"mensaje": "Observación guardada/actualizada"}
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
