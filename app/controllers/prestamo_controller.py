from app.database import get_connection

def obtener_prestamos():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = '''
            SELECT p.id, p.profesor_id, pr.nombre, pr.apellido, p.monto, p.fecha, p.estado, p.notas 
            FROM prestamos p
            JOIN profesor pr ON p.profesor_id = pr.id
            ORDER BY p.fecha DESC, p.id DESC
        '''
        cursor.execute(query)
        prestamos = cursor.fetchall()
        return [
            {
                "id": p[0], 
                "profesor_id": p[1], 
                "profesor_nombre": f"{p[3]} {p[2]}", # Apellido Nombre
                "monto": float(p[4]), 
                "fecha": str(p[5]), 
                "estado": p[6], 
                "notas": p[7]
            } for p in prestamos
        ]
    finally:
        cursor.close()
        conn.close()

def crear_prestamo(datos):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO prestamos (profesor_id, monto, fecha, estado, notas) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (datos.profesor_id, datos.monto, datos.fecha, datos.estado, datos.notas)
        )
        prestamo_id = cursor.fetchone()[0]
        conn.commit()
        return {"id": prestamo_id, "mensaje": "Préstamo registrado exitosamente"}
    finally:
        cursor.close()
        conn.close()

def actualizar_estado_prestamo(prestamo_id, estado):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE prestamos SET estado = %s WHERE id = %s", (estado, prestamo_id))
        conn.commit()
        return {"mensaje": f"Estado actualizado a {estado}"}
    finally:
        cursor.close()
        conn.close()

def eliminar_prestamo(prestamo_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM prestamos WHERE id = %s", (prestamo_id,))
        conn.commit()
        return {"mensaje": "Préstamo eliminado"}
    finally:
        cursor.close()
        conn.close()