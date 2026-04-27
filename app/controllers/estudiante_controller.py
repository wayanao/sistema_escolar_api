from app.database import get_connection

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

        # Deudas por concepto
        cursor.execute("SELECT id, nombre, valor FROM tipos_de_pagos ORDER BY id")
        tipos_pago = cursor.fetchall()
        tipos_list = [{"id": tp[0], "nombre": tp[1], "valor": float(tp[2] or 0)} for tp in tipos_pago]

        # Datos del estudiante para calcular matrícula y mensualidad
        cursor.execute('''
            SELECT c.matricula, c.mensualidad, c.meses,
                   e.descuento_matricula, e.descuento_mensualidad
            FROM estudiantes e 
            JOIN cursos c ON e.curso_id = c.id 
            WHERE e.id = %s 
        ''', (est_id,))
        est_data = cursor.fetchone()
        
        if est_data:
            matricula, mensualidad, meses, desc_mat, desc_men = est_data
            
            # Pagos del estudiante
            cursor.execute('''
                SELECT tipo_pago, COALESCE(SUM(monto), 0) 
                FROM pagos 
                WHERE estudiante_id = %s 
                GROUP BY tipo_pago
            ''', (est_id,))
            pagos_dict_por_nombre = {str(row[0]).lower(): float(row[1]) for row in cursor.fetchall()}
            
            # También agrupado por concepto_id, si tuvieran
            cursor.execute('''
                SELECT descripcion, COALESCE(SUM(monto), 0) FROM pagos 
                WHERE estudiante_id = %s GROUP BY descripcion
            ''', (est_id,))
            pagos_dict_por_desc = {str(row[0]).lower(): float(row[1]) for row in cursor.fetchall() if row[0]}
            
            deudas = []
            total_deuda = 0
            
            for tp in tipos_list:
                tp_nombre = tp['nombre']
                
                # Obtenemos el valor a cobrar
                valor_cobrado = tp['valor']
                if tp_nombre.lower() in ['matricula', 'matrícula']:
                    base_mat = tp['valor'] if tp['valor'] > 0 else (matricula or 0)
                    valor_cobrado = float(base_mat) - float(desc_mat or 0)
                elif tp_nombre.lower() in ['pension', 'mensualidad', 'pensión', 'colegiatura']:
                    base_men = tp['valor'] if tp['valor'] > 0 else (mensualidad or 0)
                    meses_totales = int(meses or 10)
                    meses_transcurridos = min(datetime.datetime.now().month, meses_totales)
                    valor_cobrado = float((base_men - float(desc_men or 0)) * meses_transcurridos)

                # Buscaríamos el pago por nombre en `tipo_pago` o en `descripcion`
                pagado = pagos_dict_por_nombre.get(tp_nombre.lower(), 0.0)
                if pagado == 0.0:
                    pagado = pagos_dict_por_desc.get(tp_nombre.lower(), 0.0)
                
                debe = max(0.0, valor_cobrado - pagado)
                
                if debe > 0:
                    deudas.append({
                        'concepto': tp_nombre,
                        'valor_total': valor_cobrado,
                        'pagado': pagado,
                        'deuda': debe
                    })
                    total_deuda += debe

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




