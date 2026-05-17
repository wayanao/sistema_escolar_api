from app.database import get_connection
from app.services.cartera import calcular_deuda_concepto

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
                COALESCE(p.fecha, p.fecha_pago::timestamp) AS fecha,
                p.descripcion,
                p.tipo_pago
            FROM pagos p
            LEFT JOIN estudiantes e ON p.estudiante_id = e.id
            WHERE TO_CHAR(COALESCE(p.fecha, p.fecha_pago::timestamp), 'YYYY-MM') = %s
            ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
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
        # 1. Detectar columnas avanzadas y tabla puente
        cursor.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = ANY (current_schemas(false))
              AND table_name = 'tipos_de_pagos'
            """
        )
        cols_tp = {row[0] for row in cursor.fetchall()}

        def _col(name, default_sql):
            return name if name in cols_tp else default_sql

        cursor.execute(
            f"""
            SELECT id, nombre, valor,
                {_col('tipo_cobro', "'unico'")} AS tipo_cobro,
                {_col('activo', 'TRUE')} AS activo,
                {_col('mes_inicial', 'NULL')} AS mes_inicial,
                {_col('frecuencia_meses', '1')} AS frecuencia_meses,
                {_col('dia_limite_mes', 'NULL')} AS dia_limite_mes,
                {_col('dias_gracia', '0')} AS dias_gracia,
                {_col('mora_tipo', 'NULL')} AS mora_tipo,
                {_col('mora_valor', '0')} AS mora_valor
            FROM tipos_de_pagos ORDER BY id
            """
        )
        tipos_pago = cursor.fetchall()
        tipos_list = [
            {
                "id": tp[0],
                "nombre": tp[1],
                "valor": float(tp[2] or 0),
                "tipo_cobro": tp[3] or "unico",
                "activo": bool(tp[4]) if tp[4] is not None else True,
                "mes_inicial": tp[5],
                "frecuencia_meses": int(tp[6]) if tp[6] is not None else 1,
                "dia_limite_mes": tp[7],
                "dias_gracia": int(tp[8]) if tp[8] is not None else 0,
                "mora_tipo": tp[9],
                "mora_valor": float(tp[10] or 0),
            }
            for tp in tipos_pago
        ]

        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = ANY (current_schemas(false))
              AND table_name = 'tipos_pagos_cursos'
            """
        )
        tabla_puente_existe = cursor.fetchone() is not None

        # Asignaciones por tipo de pago para ESTE curso y conjunto global
        valor_por_tipo_en_curso = {}
        tipos_con_alguna_asignacion = set()
        if tabla_puente_existe:
            cursor.execute(
                """
                SELECT tipo_pago_id, valor
                FROM tipos_pagos_cursos
                WHERE curso_id = %s AND activo = TRUE
                """,
                (curso_id,),
            )
            valor_por_tipo_en_curso = {row[0]: float(row[1] or 0) for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT tipo_pago_id FROM tipos_pagos_cursos")
            tipos_con_alguna_asignacion = {row[0] for row in cursor.fetchall()}

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

            # Pagos por concepto_id y también por nombre/desc (fallback)
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

            deudas_detalle = []
            total_adeudado = 0
            total_pagado_general = 0

            for tp in tipos_list:
                tp_id = tp['id']
                tp_nombre = tp['nombre']
                tp_nombre_lower = tp_nombre.lower()
                tipo_cobro = (tp['tipo_cobro'] or 'unico').lower()

                # Mismas reglas de cartera que en estudiante_controller.
                if not tp['activo'] or tipo_cobro == 'opcional':
                    continue

                es_legacy_matricula = tp_nombre_lower in ('matricula', 'matrícula')
                es_legacy_mensualidad = tp_nombre_lower in ('pension', 'pensión', 'mensualidad', 'colegiatura')
                es_legacy = es_legacy_matricula or es_legacy_mensualidad
                tiene_asignacion_en_este_curso = tp_id in valor_por_tipo_en_curso

                if not tiene_asignacion_en_este_curso and not es_legacy:
                    # No asignado al curso y no es legacy → no genera deuda.
                    continue

                # Valor unitario
                if tiene_asignacion_en_este_curso:
                    valor_unitario = valor_por_tipo_en_curso[tp_id]
                elif es_legacy_matricula:
                    valor_unitario = float((matricula or 0) - (desc_mat or 0))
                else:  # es_legacy_mensualidad
                    valor_unitario = float((mensualidad or 0) - (desc_men or 0))

                pagado = pagos_dict.get(tp_id, 0.0)
                if pagado == 0.0:
                    pagado = pagos_por_nombre.get(tp_nombre_lower, 0.0)

                resultado = calcular_deuda_concepto(
                    valor_unitario=valor_unitario,
                    tipo_cobro=tipo_cobro,
                    pagado=pagado,
                    mes_inicial=tp.get('mes_inicial'),
                    frecuencia_meses=tp.get('frecuencia_meses', 1),
                    dia_limite_mes=tp.get('dia_limite_mes'),
                    dias_gracia=tp.get('dias_gracia', 0),
                    max_cuotas=int(meses or 10),
                    mora_tipo=tp.get('mora_tipo'),
                    mora_valor=tp.get('mora_valor', 0),
                    es_legacy_mensualidad=es_legacy_mensualidad,
                )

                total_adeudado += resultado['deuda']
                total_pagado_general += resultado['pagado']

                deudas_detalle.append({
                    "concepto": tp_nombre,
                    "valor_total": resultado['valor_total'],
                    "pagado": resultado['pagado'],
                    "deuda": resultado['deuda'],
                    "mora": resultado['mora'],
                    "cuotas_vencidas": resultado['cuotas_vencidas'],
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

