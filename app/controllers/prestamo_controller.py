from datetime import date

from app.database import get_connection


def obtener_prestamos(profesor_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        filtros = []
        params = []

        if profesor_id:
            filtros.append("p.profesor_id = %s")
            params.append(profesor_id)

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""
        query = '''
            SELECT p.id, p.profesor_id, pr.nombre, pr.apellido, p.monto, p.fecha, p.estado, p.notas 
            FROM prestamos p
            JOIN profesor pr ON p.profesor_id = pr.id
            {where_sql}
            ORDER BY p.fecha DESC, p.id DESC
        '''.format(where_sql=where_sql)
        cursor.execute(query, params)
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


def _normalizar_prestamo(datos):
    profesor_id = int(datos.profesor_id or 0)
    monto = float(datos.monto)
    fecha = datos.fecha or date.today()
    notas = (datos.notas or "").strip()
    estado = (datos.estado or "Pendiente").strip()

    if profesor_id <= 0:
        raise ValueError("Debes seleccionar un profesor valido.")

    if monto <= 0:
        raise ValueError("El monto del prestamo debe ser mayor que 0.")

    if estado != "Pendiente":
        raise ValueError("Un prestamo nuevo debe iniciar en estado Pendiente.")

    return {
        "profesor_id": profesor_id,
        "monto": monto,
        "fecha": fecha,
        "estado": estado,
        "notas": notas,
    }


def crear_prestamo(datos):
    prestamo = _normalizar_prestamo(datos)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO prestamos (profesor_id, monto, fecha, estado, notas) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (
                prestamo["profesor_id"],
                prestamo["monto"],
                prestamo["fecha"],
                prestamo["estado"],
                prestamo["notas"],
            ),
        )
        prestamo_id = cursor.fetchone()[0]
        conn.commit()
        return {"id": prestamo_id, "mensaje": "Préstamo registrado exitosamente"}
    finally:
        cursor.close()
        conn.close()

def actualizar_estado_prestamo(prestamo_id, estado):
    estado_normalizado = (estado or "").strip()
    if estado_normalizado != "Pagado":
        raise ValueError("Solo se permite saldar un prestamo.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE prestamos SET estado = %s WHERE id = %s",
            (estado_normalizado, prestamo_id),
        )
        if cursor.rowcount == 0:
            raise LookupError("Prestamo no encontrado.")
        conn.commit()
        return {"mensaje": f"Estado actualizado a {estado_normalizado}"}
    finally:
        cursor.close()
        conn.close()

def eliminar_prestamo(prestamo_id):
    return {
        "error": (
            "Los prestamos no se eliminan fisicamente. "
            "Solo se pueden saldar para conservar trazabilidad."
        )
    }
