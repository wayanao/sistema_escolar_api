from app.database import get_connection


# 🎯 Validar que la asignación existe
def validar_asignacion(asignacion_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM asignaciones
        WHERE id = %s
    """, (asignacion_id,))

    existe = cursor.fetchone()

    cursor.close()
    conn.close()

    return existe is not None


# 🎯 Validar que el estudiante existe
def validar_estudiante(estudiante_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM estudiantes
        WHERE id = %s
    """, (estudiante_id,))

    existe = cursor.fetchone()

    cursor.close()
    conn.close()

    return existe is not None


# 🎯 Validar que el estudiante pertenece al curso de la asignación (PRO 🔥)
def validar_estudiante_en_curso(estudiante_id, asignacion_id):

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