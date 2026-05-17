from app.database import get_connection
from app.services.cartera import calcular_deuda_concepto

# 🎯 Crear estudiante
def crear_estudiante_controller(est):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO estudiantes 
        (
            nombre, 
            apellido,
            documento_identidad,
            fecha_nacimiento,
            curso_id, 
            descuento_matricula, 
            descuento_mensualidad,
            datos_medicos,
            telefono,
            email,
            direccion,
            nombre_padre,
            telefono_padre,
            nombre_madre,
            telefono_madre,
            contacto_emergencia,
            tipo_documento,
            lugar_expedicion,
            eps,
            estrato,
            jornada,
            colegio_anterior,
            anio_cursado_anterior,
            pre_escolar_anterior,
            ebp_anterior,
            motivo_retiro_anterior,
            paz_salvo_anterior,
            ocupacion_padre,
            tipo_documento_padre,
            documento_padre,
            ocupacion_madre,
            tipo_documento_madre,
            documento_madre,
            condicion_diagnostico
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        est.nombre,
        est.apellido,
        est.documento_identidad,
        est.fecha_nacimiento,
        est.curso_id,
        est.descuento_matricula,
        est.descuento_mensualidad,
        est.datos_medicos,
        est.telefono,
        est.email,
        est.direccion,
        est.nombre_padre,
        est.telefono_padre,
        est.nombre_madre,
        est.telefono_madre,
        est.contacto_emergencia,
        est.tipo_documento,
        est.lugar_expedicion,
        est.eps,
        est.estrato,
        est.jornada,
        est.colegio_anterior,
        est.anio_cursado_anterior,
        est.pre_escolar_anterior,
        est.ebp_anterior,
        est.motivo_retiro_anterior,
        est.paz_salvo_anterior,
        est.ocupacion_padre,
        est.tipo_documento_padre,
        est.documento_padre,
        est.ocupacion_madre,
        est.tipo_documento_madre,
        est.documento_madre,
        est.condicion_diagnostico
    ))

    estudiante_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return {
    "mensaje": "Estudiante creado correctamente",
    "id": estudiante_id
}


# 🎯 Obtener todos los estudiantes
def obtener_estudiantes_controller():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nombre, apellido, documento_identidad, fecha_nacimiento, curso_id
        FROM estudiantes
        ORDER BY apellido ASC, nombre ASC
    """)

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    data = []

    for row in resultado:
        data.append({
            "id": row[0],
            "nombre": row[1],
            "apellido": row[2],
            "documento": row[3],
            "fecha_nacimiento": str(row[4]),
            "curso_id": row[5]
        })

    return data


def actualizar_estudiante_controller(est_id, est):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE estudiantes 
        SET nombre = %s, 
            apellido = %s,
            documento_identidad = %s,
            fecha_nacimiento = %s,
            curso_id = %s, 
            descuento_matricula = %s, 
            descuento_mensualidad = %s,
            datos_medicos = %s,
            telefono = %s,
            email = %s,
            direccion = %s,
            nombre_padre = %s,
            telefono_padre = %s,
            nombre_madre = %s,
            telefono_madre = %s,
            contacto_emergencia = %s,
            tipo_documento = %s,
            lugar_expedicion = %s,
            eps = %s,
            estrato = %s,
            jornada = %s,
            colegio_anterior = %s,
            anio_cursado_anterior = %s,
            pre_escolar_anterior = %s,
            ebp_anterior = %s,
            motivo_retiro_anterior = %s,
            paz_salvo_anterior = %s,
            ocupacion_padre = %s,
            tipo_documento_padre = %s,
            documento_padre = %s,
            ocupacion_madre = %s,
            tipo_documento_madre = %s,
            documento_madre = %s,
            condicion_diagnostico = %s
        WHERE id = %s
        RETURNING id
    """, (
        est.nombre,
        est.apellido,
        est.documento_identidad,
        est.fecha_nacimiento,
        est.curso_id,
        est.descuento_matricula,
        est.descuento_mensualidad,
        est.datos_medicos,
        est.telefono,
        est.email,
        est.direccion,
        est.nombre_padre,
        est.telefono_padre,
        est.nombre_madre,
        est.telefono_madre,
        est.contacto_emergencia,
        est.tipo_documento,
        est.lugar_expedicion,
        est.eps,
        est.estrato,
        est.jornada,
        est.colegio_anterior,
        est.anio_cursado_anterior,
        est.pre_escolar_anterior,
        est.ebp_anterior,
        est.motivo_retiro_anterior,
        est.paz_salvo_anterior,
        est.ocupacion_padre,
        est.tipo_documento_padre,
        est.documento_padre,
        est.ocupacion_madre,
        est.tipo_documento_madre,
        est.documento_madre,
        est.condicion_diagnostico,
        est_id
    ))

    resultado = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    if resultado:
        return {"mensaje": "Estudiante actualizado correctamente", "id": resultado[0]}
    else:
        return {"mensaje": "Estudiante no encontrado"}

def obtener_estudiante_por_id_controller(est_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM estudiantes WHERE id = %s", (est_id,))
    row = cursor.fetchone()
    if row:
        col_names = [desc[0] for desc in cursor.description]
        data = dict(zip(col_names, row))
        # Format date for JSON response if available
        if data.get('fecha_nacimiento'):
            data['fecha_nacimiento'] = str(data['fecha_nacimiento'])
        # Also ensure numeric things are numeric if need be
        for key in ['descuento_matricula', 'descuento_mensualidad']:
            if data.get(key) is not None:
                data[key] = float(data[key])
        return data
        
    cursor.close()
    conn.close()
    return None

import datetime

def obtener_detalles_estudiante_controller(est_id):
    conn = get_connection()
    cursor = conn.cursor()
    detalles = {}
    
    try:
        # Notas por materia (promediando los detalles de la planilla)
        cursor.execute('''
            SELECT m.nombre, ROUND(AVG(n.nota), 1) as promedio
            FROM notas_detalle n
            JOIN asignaciones a ON n.asignacion_id = a.id
            JOIN materias m ON a.materia_id = m.id
            WHERE n.estudiante_id = %s GROUP BY m.id
        ''', (est_id,))
        
        notas_list = [{'materia': r[0], 'promedio': float(r[1])} for r in cursor.fetchall()]
        detalles['notas'] = notas_list
        
        if notas_list:
            promedio_gen = sum(n['promedio'] for n in notas_list) / len(notas_list)
            detalles['promedio_general'] = round(promedio_gen, 1)
        else:
            detalles['promedio_general'] = 0.0

        # Inasistencias
        cursor.execute('''
            SELECT count(*) FROM asistencia
            WHERE estudiante_id = %s AND estado ILIKE 'ausente'
        ''', (est_id,))
        detalles['inasistencias'] = cursor.fetchone()[0]

        # Observaciones (conductual, cognitivo, lenguaje)
        cursor.execute('''
            SELECT o.id, o.periodo, o.conductual, o.cognitivo, o.lenguaje, m.nombre AS materia_nombre, p.nombre || ' ' || p.apellido AS profesor_nombre FROM observaciones o JOIN asignaciones a ON o.asignacion_id = a.id JOIN materias m ON a.materia_id = m.id JOIN profesor p ON a.profesor_id = p.id WHERE o.estudiante_id = %s ORDER BY o.periodo DESC
        ''', (est_id,))
        
        obs_list = []
        for r in cursor.fetchall():
            obs_list.append({
                'id': r[0],
                'periodo': r[1],
                'conductual': r[2],
                'cognitivo': r[3],
                'lenguaje': r[4],
                'materia': r[5],
                'profesor': r[6]
            })
        detalles['observaciones'] = obs_list

        # Deudas por concepto (con soporte para tipos_pagos_cursos y config avanzada)
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

        # ¿Existe la tabla puente?
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = ANY (current_schemas(false))
              AND table_name = 'tipos_pagos_cursos'
            """
        )
        tabla_puente_existe = cursor.fetchone() is not None

        # Datos del estudiante para calcular matrícula y mensualidad
        cursor.execute('''
            SELECT c.id, c.matricula, c.mensualidad, c.meses,
                   e.descuento_matricula, e.descuento_mensualidad
            FROM estudiantes e
            JOIN cursos c ON e.curso_id = c.id
            WHERE e.id = %s
        ''', (est_id,))
        est_data = cursor.fetchone()

        if est_data:
            curso_id, matricula, mensualidad, meses, desc_mat, desc_men = est_data

            # Mapas para asignaciones del curso y tipos que tienen al menos
            # una asignación en cualquier curso.
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
                valor_por_tipo_en_curso = {
                    row[0]: float(row[1] or 0) for row in cursor.fetchall()
                }

                cursor.execute("SELECT DISTINCT tipo_pago_id FROM tipos_pagos_cursos")
                tipos_con_alguna_asignacion = {row[0] for row in cursor.fetchall()}

            # Pagos del estudiante
            cursor.execute('''
                SELECT tipo_pago, COALESCE(SUM(monto), 0)
                FROM pagos
                WHERE estudiante_id = %s
                GROUP BY tipo_pago
            ''', (est_id,))
            pagos_dict_por_nombre = {str(row[0]).lower(): float(row[1]) for row in cursor.fetchall()}

            cursor.execute('''
                SELECT descripcion, COALESCE(SUM(monto), 0) FROM pagos
                WHERE estudiante_id = %s GROUP BY descripcion
            ''', (est_id,))
            pagos_dict_por_desc = {str(row[0]).lower(): float(row[1]) for row in cursor.fetchall() if row[0]}

            deudas = []
            total_deuda = 0

            for tp in tipos_list:
                tp_id = tp['id']
                tp_nombre = tp['nombre']
                tp_nombre_lower = tp_nombre.lower()
                tipo_cobro = (tp['tipo_cobro'] or 'unico').lower()

                # ============================================================
                # REGLAS DE CARTERA — un tipo de pago SOLO genera deuda si
                # cumple TODAS estas condiciones:
                #   1. Está activo.
                #   2. Su tipo_cobro NO es 'opcional' (los opcionales se
                #      cobran solo bajo demanda, ej. certificados).
                #   3. O bien fue explícitamente asignado a este curso vía
                #      `tipos_pagos_cursos`, O bien es un concepto legacy
                #      (matrícula/pensión) que toma datos del curso.
                # ============================================================
                if not tp['activo'] or tipo_cobro == 'opcional':
                    continue

                es_legacy_matricula = tp_nombre_lower in ('matricula', 'matrícula')
                es_legacy_mensualidad = tp_nombre_lower in ('pension', 'pensión', 'mensualidad', 'colegiatura')
                es_legacy = es_legacy_matricula or es_legacy_mensualidad
                tiene_asignacion_en_este_curso = tp_id in valor_por_tipo_en_curso

                if tiene_asignacion_en_este_curso:
                    # OK: el admin asignó explícitamente este concepto a este curso.
                    pass
                elif es_legacy:
                    # OK: concepto legacy del colegio (usa cursos.matricula / mensualidad).
                    pass
                else:
                    # No asignado y no es legacy → NO genera deuda. El admin debe
                    # asignarlo a uno o más cursos desde "⚙️ Configurar".
                    continue

                # ---------- Valor unitario ----------
                if tiene_asignacion_en_este_curso:
                    valor_unitario = valor_por_tipo_en_curso[tp_id]
                elif es_legacy_matricula:
                    base_mat = tp['valor'] if tp['valor'] > 0 else (matricula or 0)
                    valor_unitario = float(base_mat) - float(desc_mat or 0)
                else:  # es_legacy_mensualidad
                    base_men = tp['valor'] if tp['valor'] > 0 else (mensualidad or 0)
                    valor_unitario = float(base_men) - float(desc_men or 0)

                # ---------- Pagos aplicados ----------
                pagado = pagos_dict_por_nombre.get(tp_nombre_lower, 0.0)
                if pagado == 0.0:
                    pagado = pagos_dict_por_desc.get(tp_nombre_lower, 0.0)

                # ---------- Cálculo de deuda (respetando configuración) ----------
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

                if resultado['deuda'] > 0:
                    deudas.append({
                        'concepto': tp_nombre,
                        'valor_total': resultado['valor_total'],
                        'pagado': resultado['pagado'],
                        'deuda': resultado['deuda'],
                        'mora': resultado['mora'],
                        'cuotas_vencidas': resultado['cuotas_vencidas'],
                    })
                    total_deuda += resultado['deuda']

            detalles['deudas'] = deudas
            detalles['total_deuda'] = total_deuda

            # Obtener productos del inventario (ventas al estudiante)
            cursor.execute('''
                SELECT v.id, v.fecha, v.estado, i.nombre, vd.cantidad, vd.subtotal, COALESCE(v.pagado, 0)
                FROM ventas v
                JOIN ventas_detalle vd ON v.id = vd.venta_id
                JOIN inventario i ON vd.inventario_id = i.id
                WHERE v.estudiante_id = %s
                ORDER BY v.fecha DESC
            ''', (est_id,))
            
            productos_inventario = []
            for v_row in cursor.fetchall():
                # Si está pendiente pero tiene abonos, calcular saldo
                estado_real = v_row[2]
                subtotal = float(v_row[5])
                pagado = float(v_row[6])
                saldo = subtotal - pagado if estado_real == 'Pendiente' else 0
                if estado_real == 'Pendiente' and pagado > 0:
                    estado_real = 'Pendiente (Abonado)'

                productos_inventario.append({
                    "venta_id": v_row[0],
                    "fecha": v_row[1].strftime('%Y-%m-%d') if v_row[1] else "",
                    "estado": estado_real,
                    "producto": v_row[3],
                    "cantidad": v_row[4],
                    "subtotal": subtotal,
                    "saldo": saldo
                })
            detalles['productos_inventario'] = productos_inventario

        else:
            detalles['deudas'] = []
            detalles['total_deuda'] = 0
            detalles['productos_inventario'] = []

        return detalles
    except Exception as e:
        print(f"Error en obtener_detalles_estudiante_controller: {e}")
        return {
            "notas": [],
            "inasistencias": 0,
            "observaciones": [],
            "deudas": [],
            "total_deuda": 0,
            "productos_inventario": []
        }
    finally:
        cursor.close()
        conn.close()




