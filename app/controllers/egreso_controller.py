from app.database import get_connection

def obtener_egresos():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, concepto, monto, fecha, categoria, notas FROM egresos ORDER BY fecha DESC, id DESC")
        egresos = cursor.fetchall()
        return [{"id": e[0], "concepto": e[1], "monto": float(e[2]), "fecha": e[3], "categoria": e[4], "notas": e[5]} for e in egresos]
    finally:
        cursor.close()
        conn.close()

def crear_egreso(datos):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO egresos (concepto, monto, fecha, categoria, notas) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (datos.concepto, datos.monto, datos.fecha, datos.categoria, datos.notas)
        )
        egreso_id = cursor.fetchone()[0]
        conn.commit()
        return {"id": egreso_id, "mensaje": "Egreso registrado exitosamente"}
    finally:
        cursor.close()
        conn.close()

def eliminar_egreso(egreso_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM egresos WHERE id = %s", (egreso_id,))
        conn.commit()
        return {"mensaje": "Egreso eliminado"}
    finally:
        cursor.close()
        conn.close()