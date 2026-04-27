from app.database import get_connection

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
                (SELECT COALESCE(SUM(monto), 0) FROM pagos WHERE DATE(fecha) = CURRENT_DATE) as ingresos_hoy
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
                TO_CHAR(fecha, 'YYYY-MM') as mes,
                SUM(monto) as total
            FROM pagos
            WHERE fecha >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(fecha, 'YYYY-MM')
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
def reporte_ingresos_mes_controller(mes: str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                p.id,
                e.nombre,
                e.apellido,
                p.monto,
                p.fecha,
                p.descripcion,
                p.tipo_pago
            FROM pagos p
            LEFT JOIN estudiantes e ON p.estudiante_id = e.id
            WHERE TO_CHAR(p.fecha, 'YYYY-MM') = %s
            ORDER BY p.fecha DESC
        """, (mes,))

        resultados = cursor.fetchall()

        return [
            {
                "id": row[0],
                "estudiante": f"{row[1]} {row[2]}" if row[1] else "Desconocido",
                "monto": float(row[3]),
                "fecha": row[4].strftime("%d/%m/%Y %H:%M") if row[4] else None,
                "descripcion": row[5] or "Sin descripción",
                "tipo_pago": row[6] if len(row) > 6 else None
            }
            for row in resultados
        ]
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
        # 1. Obtener todos los tipos de pago
        cursor.execute("SELECT id, nombre, valor FROM tipos_de_pagos ORDER BY id")
        tipos_pago = cursor.fetchall()
        tipos_list = [{"id": tp[0], "nombre": tp[1], "valor": float(tp[2] or 0)} for tp in tipos_pago]

        # 2. Obtener los estudiantes del curso
        cursor.execute('''
            SELECT e.id, e.nombre, e.apellido, 
                   c.matricula, c.mensualidad, c.meses,
                   e.descuento_matricula, e.descuento_mensualidad
            FROM estudiantes e 
            JOIN cursos c ON e.curso_id = c.id 
            WHERE e.curso_id = %s 
            ORDER BY e.apellido, e.nombre
        ''', (curso_id,))
        estudiantes = cursor.fetchall()

        resultados = []

        # 3. Calcular la deuda detallada para cada estudiante
        for est in estudiantes:
            est_id, nombre, apellido, matricula, mensualidad, meses, desc_mat, desc_men = est
            
            # Obtener pagos para poder desglosar
            cursor.execute('''
                SELECT concepto_id, COALESCE(SUM(monto), 0) 
                FROM pagos 
                WHERE estudiante_id = %s 
                GROUP BY concepto_id
            ''', (est_id,))
            pagos_dict = {row[0]: float(row[1]) for row in cursor.fetchall()}
            
            deudas_detalle = []
            total_adeudado = 0
            total_pagado_general = 0
            
            for tp in tipos_list:
                tp_id = tp['id']
                tp_nombre = tp['nombre']
                
                # Caso especial: Pension/Matricula podrian no estar en tipos_de_pagos
                # o si lo estan, su valor se toma de la configuracion del curso
                valor_cobrado = tp['valor']
                if tp_nombre.lower() == 'matricula':
                    valor_cobrado = float(matricula - desc_mat)
                elif tp_nombre.lower() == 'pension' or tp_nombre.lower() == 'mensualidad':
                    valor_cobrado = float((mensualidad - desc_men) * meses)
                    
                pagado = pagos_dict.get(tp_id, 0.0)
                deuda = max(0, valor_cobrado - pagado)
                
                total_adeudado += deuda
                total_pagado_general += pagado
                
                deudas_detalle.append({
                    "concepto": tp_nombre,
                    "valor_total": valor_cobrado,
                    "pagado": pagado,
                    "deuda": deuda
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
def reporte_ingresos_rango_controller(fecha_inicio: str, fecha_fin: str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                p.id,
                e.nombre,
                e.apellido,
                p.monto,
                p.fecha,
                p.descripcion,
                p.tipo_pago
            FROM pagos p
            LEFT JOIN estudiantes e ON p.estudiante_id = e.id
            WHERE p.fecha >= %s::date AND p.fecha < %s::date + interval '1 day'
            ORDER BY p.fecha DESC
        """, (fecha_inicio, fecha_fin))

        resultados = cursor.fetchall()

        return [
            {
                "id": row[0],
                "estudiante": f"{row[1]} {row[2]}" if row[1] else "Desconocido",
                "monto": float(row[3]),
                "fecha": row[4].strftime("%d/%m/%Y %H:%M") if row[4] else None,
                "descripcion": row[5] or "Sin descripción",
                "tipo_pago": row[6] if len(row) > 6 else None
            }
            for row in resultados
        ]
    except Exception as e:
        print(f"Error en reporte_ingresos_rango_controller: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

