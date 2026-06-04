from datetime import date

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
            SELECT id, concepto, monto, fecha, categoria, notas, COALESCE(origen, 'manual')
            FROM egresos
            {where_sql}
            ORDER BY fecha DESC, id DESC
            """,
            params,
        )
        egresos = cursor.fetchall()
        return [
            {
                "id": e[0],
                "concepto": e[1],
                "monto": float(e[2]),
                "fecha": e[3],
                "categoria": e[4],
                "notas": e[5],
                "origen": e[6],
                "editable": e[6] == "manual",
            }
            for e in egresos
        ]
    finally:
        cursor.close()
        conn.close()

def _normalizar_egreso(datos):
    concepto = (datos.concepto or "").strip()
    categoria = (datos.categoria or "Otros").strip()
    notas = (datos.notas or "").strip()
    monto = float(datos.monto)
    fecha = datos.fecha or date.today()

    if not concepto:
        raise ValueError("El concepto del egreso es obligatorio.")

    if monto <= 0:
        raise ValueError("El monto del egreso debe ser mayor que 0.")

    if not categoria:
        raise ValueError("La categoria del egreso es obligatoria.")

    return {
        "concepto": concepto,
        "monto": monto,
        "fecha": fecha,
        "categoria": categoria,
        "notas": notas,
    }


def crear_egreso(datos):
    egreso = _normalizar_egreso(datos)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO egresos (concepto, monto, fecha, categoria, notas, origen)
            VALUES (%s, %s, %s, %s, %s, 'manual')
            RETURNING id
            """,
            (
                egreso["concepto"],
                egreso["monto"],
                egreso["fecha"],
                egreso["categoria"],
                egreso["notas"],
            ),
        )
        egreso_id = cursor.fetchone()[0]
        conn.commit()
        return {"id": egreso_id, "mensaje": "Egreso registrado exitosamente"}
    finally:
        cursor.close()
        conn.close()


def actualizar_egreso(egreso_id, datos):
    egreso = _normalizar_egreso(datos)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COALESCE(origen, 'manual') FROM egresos WHERE id = %s",
            (egreso_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise LookupError("Egreso no encontrado.")

        if row[0] != "manual":
            raise PermissionError("Solo se pueden editar egresos creados manualmente en esta pantalla.")

        cursor.execute(
            """
            UPDATE egresos
            SET concepto = %s,
                monto = %s,
                fecha = %s,
                categoria = %s,
                notas = %s
            WHERE id = %s
            RETURNING id
            """,
            (
                egreso["concepto"],
                egreso["monto"],
                egreso["fecha"],
                egreso["categoria"],
                egreso["notas"],
                egreso_id,
            ),
        )
        cursor.fetchone()
        conn.commit()
        return {"id": egreso_id, "mensaje": "Egreso actualizado exitosamente"}
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
