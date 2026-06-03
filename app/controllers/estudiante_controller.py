from app.database import get_connection
from app.services.cobros import calcular_deudas_estudiante

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


def _formatear_estudiante_lista(row):
    return {
        "id": row[0],
        "nombre": row[1],
        "apellido": row[2],
        "documento": row[3],
        "fecha_nacimiento": str(row[4]) if row[4] else None,
        "curso_id": row[5]
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

    return [_formatear_estudiante_lista(row) for row in resultado]


def obtener_estudiantes_paginado_controller(limit=50, offset=0, busqueda=None):
    conn = get_connection()
    cursor = conn.cursor()

    condiciones = []
    parametros = []

    if busqueda:
        condiciones.append(
            """
            (
                nombre ILIKE %s OR
                apellido ILIKE %s OR
                documento_identidad ILIKE %s
            )
            """
        )
        like = f"%{busqueda}%"
        parametros.extend([like, like, like])

    where_sql = " WHERE " + " AND ".join(condiciones) if condiciones else ""

    try:
        cursor.execute("SELECT COUNT(*) FROM estudiantes" + where_sql, tuple(parametros))
        total = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT id, nombre, apellido, documento_identidad, fecha_nacimiento, curso_id
            FROM estudiantes
            """
            + where_sql
            + """
            ORDER BY apellido ASC, nombre ASC
            LIMIT %s OFFSET %s
            """,
            tuple(parametros + [limit, offset]),
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_formatear_estudiante_lista(row) for row in cursor.fetchall()],
        }
    finally:
        cursor.close()
        conn.close()


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

        resumen_cobros = calcular_deudas_estudiante(cursor, est_id)
        detalles['deudas'] = [
            deuda for deuda in resumen_cobros['deudas'] if deuda['deuda'] > 0
        ]
        detalles['total_deuda'] = sum(deuda['deuda'] for deuda in detalles['deudas'])

        if resumen_cobros:

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




