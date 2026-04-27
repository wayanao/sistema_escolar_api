from app.database import get_connection

def crear_materia_controller(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO materias (nombre)
        VALUES (%s)
    """, (data["nombre"],))

    conn.commit()

    cursor.close()
    conn.close()

    return {"mensaje": "Materia creada"}



def obtener_materias_controller():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nombre FROM materias
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id": r[0],
            "nombre": r[1]
        }
        for r in rows
    ]
def actualizar_materia_controller(materia_id, data):
    from app.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE materias
        SET nombre = %s
        WHERE id = %s
    ''', (data["nombre"], materia_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Materia actualizada correctamente"}
