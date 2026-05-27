from app.database import get_connection
from app.services.cobros import (
    calcular_deudas_desde_contexto,
    obtener_asignaciones_cobro_por_curso,
    obtener_tipos_pago,
)


def _formatear_ingreso(row):
    return {
        "id": row[0],
        "estudiante": f"{row[1]} {row[2]}" if row[1] else "Desconocido",
        "monto": float(row[3]),
        "fecha": row[4].strftime("%d/%m/%Y %H:%M") if row[4] else None,
        "descripcion": row[5] or "Sin descripción",
        "tipo_pago": row[6] if len(row) > 6 else None
    }

# 📊 Reporte general del sistema
def reporte_general_controller():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Estadísticas generales
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM estudiantes) as total_estudiantes,        
                (SELECT COUNT(*) FROM profesor) as total_profesores,
                (SELECT COUNT(*) FROM cursos) as total_cursos,
                (SELECT COUNT(*) FROM materias) as total_materias,
                (SELECT COALESCE(SUM(monto), 0) FROM pagos) as total_ingresos,
                (
                    SELECT COALESCE(SUM(monto), 0)
                    FROM pagos
                    WHERE DATE(COALESCE(fecha, fecha_pago::timestamp)) = CURRENT_DATE
                ) as ingresos_hoy
        """)

        stats = cursor.fetchone()

        # Estudiantes por curso
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

        # Ingresos por mes (últimos 6 meses) - Adaptado para PostgreSQL
        cursor.execute("""
            SELECT
                TO_CHAR(COALESCE(fecha, fecha_pago::timestamp), 'YYYY-MM') as mes,
                SUM(monto) as total
            FROM pagos
            WHERE COALESCE(fecha, fecha_pago::timestamp) >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(COALESCE(fecha, fecha_pago::timestamp), 'YYYY-MM')
            ORDER BY mes DESC
        """)

        ingresos_mensuales = cursor.fetchall()

        return {
            "estadisticas_generales": {
                "total_estudiantes": stats[0],
                "total_profesores": stats[1],
                "total_cursos": stats[2],
                "total_materias": stats[3],
                "total_ingresos": float(stats[4] or 0),
                "ingresos_hoy": float(stats[5] or 0)
            },
            "estudiantes_por_curso": [
                {"curso": row[0], "cantidad": row[1]}
                for row in estudiantes_por_curso
            ],
            "ingresos_mensuales": [
                {"mes": row[0], "total": float(row[1])}
                for row in ingresos_mensuales
            ]
        }

    except Exception as e:
        print(f"Error en reporte_general_controller: {e}")
        return {
            "estadisticas_generales": {
                "total_estudiantes": 0,
                "total_profesores": 0,
                "total_cursos": 0,
                "total_materias": 0,
                "total_ingresos": 0,
                "ingresos_hoy": 0
            },
            "estudiantes_por_curso": [],
            "ingresos_mensuales": []
        }
    finally:
        cursor.close()
        conn.close()

# 📊 Detalle de ingresos por mes
def reporte_ingresos_mes_controller(mes: str, limit=None, offset=0):
    conn = get_connection()
    cursor = conn.cursor()

    try:
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
                    p.tipo_pago
                FROM pagos p
                LEFT JOIN estudiantes e ON p.estudiante_id = e.id
                WHERE TO_CHAR(COALESCE(p.fecha, p.fecha_pago::timestamp), 'YYYY-MM') = %s
                ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
                LIMIT %s OFFSET %s
            """, (mes, limit, offset))

            resultados = cursor.fetchall()
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "items": [_formatear_ingreso(row) for row in resultados]
            }

        cursor.execute("""
            SELECT
                p.id,
                e.nombre,
                e.apellido,
                p.monto,
                COALESCE(p.fecha, p.fecha_pago::timestamp) AS fecha,
                p.descripcion,
                p.tipo_pago
            FROM pagos p
            LEFT JOIN estudiantes e ON p.estudiante_id = e.id
            WHERE TO_CHAR(COALESCE(p.fecha, p.fecha_pago::timestamp), 'YYYY-MM') = %s
            ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
        """, (mes,))

        resultados = cursor.fetchall()

        return [_formatear_ingreso(row) for row in resultados]
    except Exception as e:
        print(f"Error en reporte_ingresos_mes_controller: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# 📊 Reporte de estado de cuenta por curso
def reporte_estado_cuenta_curso_controller(curso_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        tipos_list = obtener_tipos_pago(cursor)
        valor_por_tipo_en_curso = obtener_asignaciones_cobro_por_curso(cursor, curso_id)

        # 2. Obtener los estudiantes del curso
        cursor.execute('''
            SELECT e.id, e.nombre, e.apellido
            FROM estudiantes e 
            JOIN cursos c ON e.curso_id = c.id 
            WHERE e.curso_id = %s 
            ORDER BY e.apellido, e.nombre
        ''', (curso_id,))
        estudiantes = cursor.fetchall()

        resultados = []

        # 3. Calcular la deuda detallada para cada estudiante
        for est in estudiantes:
            est_id, nombre, apellido = est

            # Pagos por concepto_id y tambien por nombre/desc (fallback)
            cursor.execute('''
                SELECT concepto_id, COALESCE(SUM(monto), 0)
                FROM pagos
                WHERE estudiante_id = %s
                GROUP BY concepto_id
            ''', (est_id,))
            pagos_dict = {row[0]: float(row[1]) for row in cursor.fetchall()}

            cursor.execute('''
                SELECT tipo_pago, COALESCE(SUM(monto), 0)
                FROM pagos WHERE estudiante_id = %s GROUP BY tipo_pago
            ''', (est_id,))
            pagos_por_nombre = {str(r[0]).lower(): float(r[1]) for r in cursor.fetchall() if r[0]}
            for tipo in tipos_list:
                nombre_tipo = str(tipo["nombre"]).lower()
                if nombre_tipo not in pagos_por_nombre and tipo["id"] in pagos_dict:
                    pagos_por_nombre[nombre_tipo] = pagos_dict[tipo["id"]]

            resumen = calcular_deudas_desde_contexto(
                tipos_pago=tipos_list,
                asignaciones_curso=valor_por_tipo_en_curso,
                pagos_nombre=pagos_por_nombre,
                pagos_descripcion={},
            )

            deudas_detalle = []
            total_adeudado = 0.0
            total_pagado_general = 0.0

            for deuda in resumen["deudas"]:
                concepto_id = deuda.get("concepto_id")
                pagado = pagos_dict.get(concepto_id, deuda["pagado"])
                total_adeudado += deuda["deuda"]
                total_pagado_general += pagado

                deudas_detalle.append({
                    "concepto": deuda["concepto"],
                    "valor_total": deuda["valor_total"],
                    "pagado": pagado,
                    "deuda": deuda["deuda"],
                    "mora": deuda["mora"],
                    "cuotas_vencidas": deuda["cuotas_vencidas"],
                })

            # Considerar pagos sin concepto especifico o conceptos eliminados
            cursor.execute('''
                SELECT COALESCE(SUM(monto), 0) 
                FROM pagos 
                WHERE estudiante_id = %s AND (concepto_id IS NULL OR concepto_id NOT IN (SELECT id FROM tipos_de_pagos))
            ''', (est_id,))
            row = cursor.fetchone()
            pagos_otros = float(row[0]) if row and row[0] else 0.0
            
            if pagos_otros > 0:
                total_pagado_general += pagos_otros
                deudas_detalle.append({
                    "concepto": "Otros Pagos",
                    "valor_total": 0,
                    "pagado": pagos_otros,
                    "deuda": -pagos_otros
                })

            # Esto mantiene retrocompatibilidad y añade el detalle de columnas dinámicas
            resultados.append({
                "id": est_id,
                "nombre": nombre,
                "apellido": apellido,
                "pagado": float(total_pagado_general),
                "total": float(total_adeudado + total_pagado_general),
                "deuda": float(total_adeudado),
                "deudas_detalle": deudas_detalle
            })

        return resultados

    except Exception as e:
        print(f"Error en reporte_estado_cuenta_curso_controller: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# 📊 Detalle de ingresos por rango de fechas
def reporte_ingresos_rango_controller(fecha_inicio: str, fecha_fin: str, limit=None, offset=0):
    conn = get_connection()
    cursor = conn.cursor()

    try:
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
                    p.tipo_pago
                FROM pagos p
                LEFT JOIN estudiantes e ON p.estudiante_id = e.id
                WHERE COALESCE(p.fecha, p.fecha_pago::timestamp) >= %s::date
                  AND COALESCE(p.fecha, p.fecha_pago::timestamp) < %s::date + interval '1 day'
                ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
                LIMIT %s OFFSET %s
            """, (fecha_inicio, fecha_fin, limit, offset))

            resultados = cursor.fetchall()
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "items": [_formatear_ingreso(row) for row in resultados]
            }

        cursor.execute("""
            SELECT
                p.id,
                e.nombre,
                e.apellido,
                p.monto,
                COALESCE(p.fecha, p.fecha_pago::timestamp) AS fecha,
                p.descripcion,
                p.tipo_pago
            FROM pagos p
            LEFT JOIN estudiantes e ON p.estudiante_id = e.id
            WHERE COALESCE(p.fecha, p.fecha_pago::timestamp) >= %s::date
              AND COALESCE(p.fecha, p.fecha_pago::timestamp) < %s::date + interval '1 day'
            ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
        """, (fecha_inicio, fecha_fin))

        resultados = cursor.fetchall()

        return [_formatear_ingreso(row) for row in resultados]
    except Exception as e:
        print(f"Error en reporte_ingresos_rango_controller: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

