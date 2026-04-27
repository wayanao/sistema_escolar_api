from app.database import get_connection


# 🎯 Crear curso
def crear_curso_controller(curso):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cursos (nombre, matricula, mensualidad, meses, jornada)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        curso.nombre,
        curso.matricula,
        curso.mensualidad,
        curso.meses,
        curso.jornada
    ))

    curso_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return curso_id 


# 🎯 Listar cursos
def obtener_cursos_controller():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nombre, matricula, mensualidad, meses, jornada
        FROM cursos
        ORDER BY id
    """)

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    data = []

    for row in resultado:
        data.append({
            "id": row[0],
            "nombre": row[1],
            "matricula": float(row[2]),
            "mensualidad": float(row[3]),
            "meses": row[4],
            "jornada": row[5] or "Mañana"
        })

    return data
def actualizar_curso_controller(curso_id, curso):
    from app.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE cursos
        SET nombre = %s, matricula = %s, mensualidad = %s, meses = %s, jornada = %s
        WHERE id = %s
    ''', (curso.nombre, curso.matricula, curso.mensualidad, curso.meses, curso.jornada, curso_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Curso actualizado correctamente"}
