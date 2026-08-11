import logging

from app.database import get_connection, get_cursor
from app.services.cobros import calcular_deudas_estudiante

logger = logging.getLogger(__name__)

ESTADOS_ESTUDIANTE = {"activo", "retirado", "egresado", "inactivo"}
ESTADOS_FILTRO_ESTUDIANTE = ESTADOS_ESTUDIANTE | {"todos"}


def normalizar_estado_estudiante(estado, default="activo"):
    valor = str(estado or default).strip().lower()
    if valor not in ESTADOS_ESTUDIANTE:
        raise ValueError("Estado de estudiante invalido")
    return valor


def _build_estado_filter(estado):
    estado_normalizado = str(estado or "activo").strip().lower()
    if estado_normalizado not in ESTADOS_FILTRO_ESTUDIANTE:
        raise ValueError("Filtro de estado de estudiante invalido")
    if estado_normalizado == "todos":
        return "", []
    return "COALESCE(LOWER(estado), 'activo') = %s", [estado_normalizado]


# 🎯 Crear estudiante
def crear_estudiante_controller(est):

    with get_cursor(commit=True) as cursor:
        estado = normalizar_estado_estudiante(getattr(est, "estado", None))

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
            condicion_diagnostico,
            estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            estado
        ))

        estudiante_id = cursor.fetchone()[0]

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
        "curso_id": row[5],
        "email": row[6],
        "estado": row[7] or "activo",
    }


# 🎯 Obtener todos los estudiantes
def obtener_estudiantes_controller(estado="activo"):

    conn = get_connection()
    cursor = conn.cursor()
    try:
        estado_where, parametros = _build_estado_filter(estado)
        where_sql = f"WHERE {estado_where}" if estado_where else ""

        cursor.execute(f"""
            SELECT
                id,
                nombre,
                apellido,
                documento_identidad,
                fecha_nacimiento,
                curso_id,
                email,
                COALESCE(LOWER(estado), 'activo') AS estado
            FROM estudiantes
            {where_sql}
            ORDER BY apellido ASC, nombre ASC
        """, tuple(parametros))

        resultado = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return [_formatear_estudiante_lista(row) for row in resultado]


def obtener_estudiantes_paginado_controller(limit=50, offset=0, busqueda=None, estado="activo"):
    conn = get_connection()
    cursor = conn.cursor()

    condiciones = []
    parametros = []
    estado_where, estado_params = _build_estado_filter(estado)
    if estado_where:
        condiciones.append(estado_where)
        parametros.extend(estado_params)

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
            SELECT
                id,
                nombre,
                apellido,
                documento_identidad,
                fecha_nacimiento,
                curso_id,
                email,
                COALESCE(LOWER(estado), 'activo') AS estado
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
    with get_cursor(commit=True) as cursor:
        estado = (
            normalizar_estado_estudiante(est.estado)
            if getattr(est, "estado", None) is not None
            else None
        )

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
            condicion_diagnostico = %s,
                estado = COALESCE(%s, estado, 'activo')
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
            estado,
            est_id
        ))

        resultado = cursor.fetchone()

    if resultado:
        return {"mensaje": "Estudiante actualizado correctamente", "id": resultado[0]}
    else:
        return {"mensaje": "Estudiante no encontrado"}

def obtener_estudiante_por_id_controller(est_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM estudiantes WHERE id = %s", (est_id,))
        row = cursor.fetchone()
        if row:
            col_names = [desc[0] for desc in cursor.description]
            data = dict(zip(col_names, row))
            # Format date for JSON response if available
            if data.get('fecha_nacimiento'):
                data['fecha_nacimiento'] = str(data['fecha_nacimiento'])
            if not data.get("estado"):
                data["estado"] = "activo"
            else:
                data["estado"] = str(data["estado"]).strip().lower()
            # Also ensure numeric things are numeric if need be
            for key in ['descuento_matricula', 'descuento_mensualidad']:
                if data.get(key) is not None:
                    data[key] = float(data[key])
            return data

        return None
    finally:
        cursor.close()
        conn.close()


def actualizar_estado_estudiante_controller(est_id, estado):
    estado_normalizado = normalizar_estado_estudiante(estado)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE estudiantes
            SET estado = %s
            WHERE id = %s
            RETURNING id, COALESCE(LOWER(estado), 'activo')
            """,
            (estado_normalizado, est_id),
        )
        row = cursor.fetchone()
        if not row:
            conn.rollback()
            return {"error": "Estudiante no encontrado"}
        conn.commit()
        return {
            "mensaje": "Estado de estudiante actualizado",
            "id": row[0],
            "estado": row[1],
        }
    finally:
        cursor.close()
        conn.close()


def obtener_deudas_estudiante_controller(est_id):
    with get_cursor() as cursor:
        resumen_cobros = calcular_deudas_estudiante(cursor, est_id)

    return _formatear_resumen_deudas(est_id, resumen_cobros)


def _formatear_resumen_deudas(est_id, resumen_cobros):
    deudas = [
        deuda for deuda in resumen_cobros["deudas"] if deuda["deuda"] > 0
    ]
    return {
        "estudiante_id": est_id,
        "curso_id": resumen_cobros.get("curso_id"),
        "deudas": deudas,
        "total_deuda": sum(deuda["deuda"] for deuda in deudas),
    }


def _registrar_error_detalle(detalles, seccion, exc):
    logger.exception("Error cargando %s del estudiante", seccion)
    detalles.setdefault("errores", {})[seccion] = "No se pudo cargar esta seccion."


def obtener_detalles_estudiante_controller(est_id):
    conn = get_connection()
    cursor = conn.cursor()
    detalles = {
        "notas": [],
        "promedio_general": 0.0,
        "inasistencias": 0,
        "observaciones": [],
        "deudas": [],
        "total_deuda": 0,
        "productos_inventario": [],
    }

    try:
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
        except Exception as exc:
            conn.rollback()
            _registrar_error_detalle(detalles, "notas", exc)

        try:
            cursor.execute('''
                SELECT count(*) FROM asistencia
                WHERE estudiante_id = %s AND estado ILIKE 'ausente'
            ''', (est_id,))
            detalles['inasistencias'] = cursor.fetchone()[0]
        except Exception as exc:
            conn.rollback()
            _registrar_error_detalle(detalles, "asistencia", exc)

        try:
            cursor.execute('''
                SELECT o.id, o.periodo, o.conductual, o.cognitivo, o.lenguaje, m.nombre AS materia_nombre, p.nombre || ' ' || p.apellido AS profesor_nombre FROM observaciones o JOIN asignaciones a ON o.asignacion_id = a.id JOIN materias m ON a.materia_id = m.id JOIN profesor p ON a.profesor_id = p.id WHERE o.estudiante_id = %s ORDER BY o.periodo DESC
            ''', (est_id,))

            detalles['observaciones'] = [
                {
                    'id': r[0],
                    'periodo': r[1],
                    'conductual': r[2],
                    'cognitivo': r[3],
                    'lenguaje': r[4],
                    'materia': r[5],
                    'profesor': r[6]
                }
                for r in cursor.fetchall()
            ]
        except Exception as exc:
            conn.rollback()
            _registrar_error_detalle(detalles, "observaciones", exc)

        try:
            resumen_cobros = _formatear_resumen_deudas(
                est_id,
                calcular_deudas_estudiante(cursor, est_id),
            )
            detalles['deudas'] = resumen_cobros["deudas"]
            detalles['total_deuda'] = resumen_cobros["total_deuda"]
        except Exception as exc:
            conn.rollback()
            _registrar_error_detalle(detalles, "deudas", exc)

        try:
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
        except Exception as exc:
            conn.rollback()
            _registrar_error_detalle(detalles, "inventario", exc)

        return detalles
    finally:
        cursor.close()
        conn.close()




