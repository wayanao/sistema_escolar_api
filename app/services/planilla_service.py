from app.database import get_connection


# 🎯 Validar que el estudiante pertenece a la asignación
def validar_estudiante_asignacion(estudiante_id, asignacion_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.id
        FROM estudiantes e
        JOIN asignaciones a ON e.curso_id = a.curso_id
        WHERE e.id = %s AND a.id = %s
    """, (estudiante_id, asignacion_id))

    existe = cursor.fetchone()

    cursor.close()
    conn.close()

    return existe is not None