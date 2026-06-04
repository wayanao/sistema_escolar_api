from app.database import get_connection

def obtener_egresos(fecha_desde=None, fecha_hasta=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        filtros = []
        params = []

        if fecha_desde:
            filtros.append("fecha::date >= %s")
            params.append(fecha_desde)

        if fecha_hasta:
            filtros.append("fecha::date <= %s")
            params.append(fecha_hasta)

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"""
            SELECT id, concepto, monto, fecha, categoria, notas
            FROM egresos
            {where_sql}
            ORDER BY fecha DESC, id DESC
            """,
            params,
        )
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
    return {
        "error": (
            "Los egresos no se eliminan fisicamente. "
            "Conserva el registro contable para trazabilidad."
        )
    }
