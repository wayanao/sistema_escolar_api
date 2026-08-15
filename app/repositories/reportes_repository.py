def consultar_reporte_general(cursor):
    cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM estudiantes) as total_estudiantes,\x20\x20\x20\x20\x20\x20\x20\x20
                (SELECT COUNT(*) FROM profesor) as total_profesores,
                (SELECT COUNT(*) FROM cursos) as total_cursos,
                (SELECT COUNT(*) FROM materias) as total_materias,
                (SELECT COALESCE(SUM(monto), 0) FROM pagos WHERE COALESCE(estado, 'Pagado') <> 'Anulado') as total_ingresos,
                (
                    SELECT COALESCE(SUM(monto), 0)
                    FROM pagos
                    WHERE DATE(COALESCE(fecha, fecha_pago::timestamp)) = (NOW() AT TIME ZONE 'America/Bogota')::date
                      AND COALESCE(estado, 'Pagado') <> 'Anulado'
                ) as ingresos_hoy,
                (SELECT COALESCE(SUM(monto), 0) FROM egresos) as total_egresos,
                (
                    SELECT COALESCE(SUM(monto), 0)
                    FROM egresos
                    WHERE fecha::date = (NOW() AT TIME ZONE 'America/Bogota')::date
                ) as egresos_hoy
        """)
    stats = cursor.fetchone()

    cursor.execute("""
            SELECT
                c.nombre as curso,
                COUNT(e.id) as cantidad_estudiantes
            FROM cursos c
            LEFT JOIN estudiantes e ON c.id = e.curso_id
            GROUP BY c.id, c.nombre
            ORDER BY c.nombre
        """)
    estudiantes_por_curso = cursor.fetchall()

    cursor.execute("""
            SELECT
                TO_CHAR(COALESCE(fecha, fecha_pago::timestamp), 'YYYY-MM') as mes,
                SUM(CASE WHEN COALESCE(estado, 'Pagado') = 'Anulado' THEN 0 ELSE monto END) as total
            FROM pagos
            WHERE COALESCE(fecha, fecha_pago::timestamp) >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(COALESCE(fecha, fecha_pago::timestamp), 'YYYY-MM')
            ORDER BY mes DESC
        """)
    ingresos_mensuales = cursor.fetchall()

    cursor.execute("""
            SELECT
                TO_CHAR(fecha::date, 'YYYY-MM') as mes,
                SUM(monto) as total
            FROM egresos
            WHERE fecha::date >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(fecha::date, 'YYYY-MM')
            ORDER BY mes DESC
        """)
    egresos_mensuales = cursor.fetchall()

    return (
        stats,
        estudiantes_por_curso,
        ingresos_mensuales,
        egresos_mensuales,
    )


def consultar_ingresos_mes(cursor, mes, limit=None, offset=0):
    if limit is not None:
        cursor.execute("""
                SELECT COUNT(*)
                FROM pagos p
                WHERE TO_CHAR(COALESCE(p.fecha, p.fecha_pago::timestamp), 'YYYY-MM') = %s
            """, (mes,))
        total = cursor.fetchone()[0]

        cursor.execute("""
                SELECT
                    p.id,
                    e.nombre,
                    e.apellido,
                    p.monto,
                    COALESCE(p.fecha, p.fecha_pago::timestamp) AS fecha,
                    p.descripcion,
                    p.tipo_pago,
                    COALESCE(p.estado, 'Pagado') AS estado,
                    p.motivo_anulacion,
                    p.fecha_anulacion
                FROM pagos p
                LEFT JOIN estudiantes e ON p.estudiante_id = e.id
                WHERE TO_CHAR(COALESCE(p.fecha, p.fecha_pago::timestamp), 'YYYY-MM') = %s
                ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
                LIMIT %s OFFSET %s
            """, (mes, limit, offset))
        return total, cursor.fetchall()

    cursor.execute("""
            SELECT
                p.id,
                e.nombre,
                e.apellido,
                p.monto,
                COALESCE(p.fecha, p.fecha_pago::timestamp) AS fecha,
                p.descripcion,
                p.tipo_pago,
                COALESCE(p.estado, 'Pagado') AS estado,
                p.motivo_anulacion,
                p.fecha_anulacion
            FROM pagos p
            LEFT JOIN estudiantes e ON p.estudiante_id = e.id
            WHERE TO_CHAR(COALESCE(p.fecha, p.fecha_pago::timestamp), 'YYYY-MM') = %s
            ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
        """, (mes,))
    return None, cursor.fetchall()


def consultar_ingresos_rango(
    cursor,
    fecha_inicio,
    fecha_fin,
    limit=None,
    offset=0,
):
    if limit is not None:
        cursor.execute("""
                SELECT COUNT(*)
                FROM pagos p
                WHERE COALESCE(p.fecha, p.fecha_pago::timestamp) >= %s::date
                  AND COALESCE(p.fecha, p.fecha_pago::timestamp) < %s::date + interval '1 day'
            """, (fecha_inicio, fecha_fin))
        total = cursor.fetchone()[0]

        cursor.execute("""
                SELECT
                    p.id,
                    e.nombre,
                    e.apellido,
                    p.monto,
                    COALESCE(p.fecha, p.fecha_pago::timestamp) AS fecha,
                    p.descripcion,
                    p.tipo_pago,
                    COALESCE(p.estado, 'Pagado') AS estado,
                    p.motivo_anulacion,
                    p.fecha_anulacion
                FROM pagos p
                LEFT JOIN estudiantes e ON p.estudiante_id = e.id
                WHERE COALESCE(p.fecha, p.fecha_pago::timestamp) >= %s::date
                  AND COALESCE(p.fecha, p.fecha_pago::timestamp) < %s::date + interval '1 day'
                ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
                LIMIT %s OFFSET %s
            """, (fecha_inicio, fecha_fin, limit, offset))
        return total, cursor.fetchall()

    cursor.execute("""
            SELECT
                p.id,
                e.nombre,
                e.apellido,
                p.monto,
                COALESCE(p.fecha, p.fecha_pago::timestamp) AS fecha,
                p.descripcion,
                p.tipo_pago,
                COALESCE(p.estado, 'Pagado') AS estado,
                p.motivo_anulacion,
                p.fecha_anulacion
            FROM pagos p
            LEFT JOIN estudiantes e ON p.estudiante_id = e.id
            WHERE COALESCE(p.fecha, p.fecha_pago::timestamp) >= %s::date
              AND COALESCE(p.fecha, p.fecha_pago::timestamp) < %s::date + interval '1 day'
            ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
        """, (fecha_inicio, fecha_fin))
    return None, cursor.fetchall()


def consultar_egresos_rango(
    cursor,
    fecha_inicio,
    fecha_fin,
    limit=None,
    offset=0,
):
    if limit is not None:
        cursor.execute("""
                SELECT COUNT(*)
                FROM egresos
                WHERE fecha::date >= %s::date
                  AND fecha::date < %s::date + interval '1 day'
            """, (fecha_inicio, fecha_fin))
        total = cursor.fetchone()[0]

        cursor.execute("""
                SELECT id, concepto, monto, fecha, categoria, notas, COALESCE(origen, 'manual') AS origen
                FROM egresos
                WHERE fecha::date >= %s::date
                  AND fecha::date < %s::date + interval '1 day'
                ORDER BY fecha DESC, id DESC
                LIMIT %s OFFSET %s
            """, (fecha_inicio, fecha_fin, limit, offset))
        return total, cursor.fetchall()

    cursor.execute("""
            SELECT id, concepto, monto, fecha, categoria, notas, COALESCE(origen, 'manual') AS origen
            FROM egresos
            WHERE fecha::date >= %s::date
              AND fecha::date < %s::date + interval '1 day'
            ORDER BY fecha DESC, id DESC
        """, (fecha_inicio, fecha_fin))
    return None, cursor.fetchall()


def consultar_estudiantes_estado_cuenta_curso(cursor, curso_id):
    cursor.execute('''
            SELECT e.id, e.nombre, e.apellido
            FROM estudiantes e\x20
            JOIN cursos c ON e.curso_id = c.id\x20
            WHERE e.curso_id = %s\x20
            ORDER BY e.apellido, e.nombre
        ''', (curso_id,))
    return cursor.fetchall()


def consultar_pagos_estado_cuenta_por_estudiantes(cursor, estudiante_ids):
    if not estudiante_ids:
        return [], []

    cursor.execute(
        """
        SELECT estudiante_id, concepto_id, COALESCE(SUM(monto), 0)
        FROM pagos
        WHERE estudiante_id IN %s
          AND COALESCE(estado, 'Pagado') <> 'Anulado'
        GROUP BY estudiante_id, concepto_id
        """,
        (estudiante_ids,),
    )
    pagos_por_concepto = cursor.fetchall()

    cursor.execute(
        """
        SELECT estudiante_id, tipo_pago, COALESCE(SUM(monto), 0)
        FROM pagos
        WHERE estudiante_id IN %s
          AND COALESCE(estado, 'Pagado') <> 'Anulado'
        GROUP BY estudiante_id, tipo_pago
        """,
        (estudiante_ids,),
    )
    pagos_por_nombre = cursor.fetchall()

    return pagos_por_concepto, pagos_por_nombre


def consultar_otros_pagos_por_estudiantes(
    cursor,
    estudiante_ids,
    tiene_aplicaciones,
):
    if not estudiante_ids:
        return []

    excluir_adelantos = """
          AND NOT EXISTS (
              SELECT 1 FROM pagos_aplicaciones pa
              WHERE pa.pago_id = pagos.id
          )
    """ if tiene_aplicaciones else ""
    cursor.execute(
        f"""
        SELECT estudiante_id, COALESCE(SUM(monto), 0)
        FROM pagos
        WHERE estudiante_id IN %s
          AND (concepto_id IS NULL OR concepto_id NOT IN (SELECT id FROM tipos_de_pagos))
          AND COALESCE(estado, 'Pagado') <> 'Anulado'
          {excluir_adelantos}
        GROUP BY estudiante_id
        """,
        (estudiante_ids,),
    )
    return cursor.fetchall()
