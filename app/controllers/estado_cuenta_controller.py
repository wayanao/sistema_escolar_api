from app.database import get_connection
from app.repositories.anios_lectivos_repository import condicion_anio
from app.services.cobros import calcular_deudas_estudiante, con_anio


def _resumen_pagos_estudiante(cursor, estudiante_id, anio_lectivo_id=None):
    # Lo pagado en un año (sin `anio_lectivo_id`, el activo), el mismo año con
    # que se calcula la deuda.
    condicion, params_anio = condicion_anio("pagos.anio_lectivo_id", anio_lectivo_id)
    cursor.execute(
        f"""
        SELECT COALESCE(SUM(monto), 0),
               STRING_AGG(DISTINCT descripcion, ', ')
        FROM pagos
        WHERE estudiante_id = %s
          AND COALESCE(estado, 'Pagado') <> 'Anulado'
          AND {condicion}
        """,
        (estudiante_id, *params_anio),
    )
    row = cursor.fetchone()
    return {
        "pagado": float(row[0] or 0) if row else 0.0,
        "tipos_pagos": row[1] if row and row[1] else "",
    }


def _estado_cuenta_estudiante(cursor, estudiante_id, nombre, apellido, anio_lectivo_id=None):
    pagos = _resumen_pagos_estudiante(cursor, estudiante_id, anio_lectivo_id)
    cobros = calcular_deudas_estudiante(cursor, estudiante_id, **con_anio(anio_lectivo_id))
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
        # Fase 3 del año lectivo: los estudiantes del curso salen de sus
        # matriculas, y la deuda y lo pagado son del año de ese curso. El año
        # viaja en la misma consulta, sin una ida mas a la base. Si es el
        # activo, `None`: las mismas consultas de siempre por estudiante.
        cursor.execute("""
            SELECT e.id, e.nombre, e.apellido, m.anio_lectivo_id, al.estado
            FROM estudiantes e
            JOIN matriculas m ON m.estudiante_id = e.id
            JOIN anios_lectivos al ON al.id = m.anio_lectivo_id
            WHERE m.curso_id = %s
            ORDER BY e.apellido, e.nombre
        """, (curso_id,))

        return [
            _estado_cuenta_estudiante(
                cursor, row[0], row[1], row[2],
                None if row[4] == "activo" else row[3],
            )
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
