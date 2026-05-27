from app.database import get_connection
from app.services.cobros import calcular_deudas_estudiante


def _resumen_pagos_estudiante(cursor, estudiante_id):
    cursor.execute(
        """
        SELECT COALESCE(SUM(monto), 0),
               STRING_AGG(DISTINCT descripcion, ', ')
        FROM pagos
        WHERE estudiante_id = %s
        """,
        (estudiante_id,),
    )
    row = cursor.fetchone()
    return {
        "pagado": float(row[0] or 0) if row else 0.0,
        "tipos_pagos": row[1] if row and row[1] else "",
    }


def _estado_cuenta_estudiante(cursor, estudiante_id, nombre, apellido):
    pagos = _resumen_pagos_estudiante(cursor, estudiante_id)
    cobros = calcular_deudas_estudiante(cursor, estudiante_id)
    deuda = float(cobros["total_deuda"] or 0)

    return {
        "id": estudiante_id,
        "nombre": nombre,
        "apellido": apellido,
        "pagado": pagos["pagado"],
        "total": deuda + pagos["pagado"],
        "deuda": deuda,
        "tipos_pagos": pagos["tipos_pagos"],
    }


# 🎯 Estado de cuenta por CURSO (lista de estudiantes)
def estado_cuenta_curso_controller(curso_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, nombre, apellido
            FROM estudiantes
            WHERE curso_id = %s
            ORDER BY apellido, nombre
        """, (curso_id,))

        return [
            _estado_cuenta_estudiante(cursor, row[0], row[1], row[2])
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conn.close()


# 🎯 Estado de cuenta por ESTUDIANTE (detalle)
def estado_cuenta_estudiante_controller(estudiante_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, nombre, apellido
            FROM estudiantes
            WHERE id = %s
        """, (estudiante_id,))

        resultado = cursor.fetchone()
        if not resultado:
            return {"mensaje": "Estudiante no encontrado"}

        return _estado_cuenta_estudiante(
            cursor,
            resultado[0],
            resultado[1],
            resultado[2],
        )
    finally:
        cursor.close()
        conn.close()
