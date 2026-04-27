from app.database import get_connection



def guardar_observacion_controller(data):

    conn = get_connection()
    cursor = conn.cursor()

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
        data["asignacion_id"],
        data["periodo"],
        data["conductual"],
        data["cognitivo"],
        data["lenguaje"]
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return {"mensaje": "Observación guardada/actualizada"}