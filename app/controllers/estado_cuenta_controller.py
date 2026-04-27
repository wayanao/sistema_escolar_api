from app.database import get_connection


# 🎯 Estado de cuenta por CURSO (lista de estudiantes)
def estado_cuenta_curso_controller(curso_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            e.id,
            e.nombre,
            e.apellido,

            COALESCE(SUM(p.monto), 0) AS pagado,

            (
                (c.matricula - e.descuento_matricula) +
                ((c.mensualidad - e.descuento_mensualidad) * c.meses)
            ) AS total,

            (
                (c.matricula - e.descuento_matricula) +
                ((c.mensualidad - e.descuento_mensualidad) * c.meses)
            ) - COALESCE(SUM(p.monto), 0) AS deuda,

            STRING_AGG(DISTINCT p.descripcion, ', ') AS tipos_pagos

        FROM estudiantes e

        JOIN cursos c ON e.curso_id = c.id

        LEFT JOIN pagos p 
        ON e.id = p.estudiante_id

        WHERE e.curso_id = %s

        GROUP BY 
            e.id, 
            e.nombre, 
            e.apellido,
            c.matricula,
            c.mensualidad,
            c.meses,
            e.descuento_matricula,
            e.descuento_mensualidad
    """, (curso_id,))

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    data = []

    for row in resultado:
        data.append({
            "id": row[0],
            "nombre": row[1],
            "apellido": row[2],
            "pagado": float(row[3]),
            "total": float(row[4]),
            "deuda": float(row[5]),
            "tipos_pagos": row[6] if row[6] else ''
        })

    return data


# 🎯 Estado de cuenta por ESTUDIANTE (detalle)
def estado_cuenta_estudiante_controller(estudiante_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            e.id,
            e.nombre,
            e.apellido,

            COALESCE(SUM(p.monto), 0) AS pagado,

            (
                (c.matricula - e.descuento_matricula) +
                ((c.mensualidad - e.descuento_mensualidad) * c.meses)
            ) AS total,

            (
                (c.matricula - e.descuento_matricula) +
                ((c.mensualidad - e.descuento_mensualidad) * c.meses)
            ) - COALESCE(SUM(p.monto), 0) AS deuda,

            STRING_AGG(DISTINCT p.descripcion, ', ') AS tipos_pagos

        FROM estudiantes e

        JOIN cursos c ON e.curso_id = c.id

        LEFT JOIN pagos p 
        ON e.id = p.estudiante_id

        WHERE e.id = %s

        GROUP BY 
            e.id, 
            e.nombre, 
            e.apellido,
            c.matricula,
            c.mensualidad,
            c.meses,
            e.descuento_matricula,
            e.descuento_mensualidad
    """, (estudiante_id,))

    resultado = cursor.fetchone()

    cursor.close()
    conn.close()

    if not resultado:
        return {"mensaje": "Estudiante no encontrado"}

    return {
        "id": resultado[0],
        "nombre": resultado[1],
        "apellido": resultado[2],
        "pagado": float(resultado[3]),
        "total": float(resultado[4]),
        "deuda": float(resultado[5]),
        "tipos_pagos": resultado[6] if resultado[6] else ''
    }
