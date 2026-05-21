from app.database import get_connection

def guardar_asistencia_controller(data):
    conn = get_connection()
    cursor = conn.cursor()

    # 🔥 PRIMERO borrar TODO del día (solo una vez)
    if len(data) > 0:
        cursor.execute("""
            DELETE FROM asistencia
            WHERE asignacion_id = %s AND fecha = %s AND periodo = %s
        """, (
            data[0].asignacion_id,
            data[0].fecha,
            data[0].periodo
        ))

    # 🔥 LUEGO insertar TODOS
    for item in data:
        cursor.execute("""
            INSERT INTO asistencia (estudiante_id, asignacion_id, fecha, estado, periodo)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            item.estudiante_id,
            item.asignacion_id,
            item.fecha,
            item.estado,
            item.periodo
        ))

    conn.commit()
    cursor.close()
    conn.close()

    return {"mensaje": "Asistencia guardada"}


def obtener_historial_asistencia(asignacion_id, periodo=1):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.id,
            e.nombre,
            e.apellido,
            a.fecha,
            a.estado
        FROM estudiantes e

        JOIN asistencia a ON a.estudiante_id = e.id

        WHERE a.asignacion_id = %s AND a.periodo = %s
        ORDER BY e.apellido ASC, e.nombre ASC, a.fecha ASC
    """, (asignacion_id, periodo))

    rows = cursor.fetchall()

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

    cursor.close()
    conn.close()

    return list(resultado.values())
