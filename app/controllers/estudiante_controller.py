import logging

from app.database import get_connection, get_cursor
from app.repositories import anios_lectivos_repository, estudiantes_repository
from app.services.anio_lectivo import exigir_anio_lectivo
from app.services.cobros import (
    calcular_deudas_anios_anteriores,
    calcular_deudas_estudiante,
    con_anio,
)

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

        estudiante_id = estudiantes_repository.insertar_estudiante(cursor, (
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
        # Fase 1 del año lectivo: su matricula del año activo, en la misma
        # transaccion.
        anios_lectivos_repository.sincronizar_matricula_del_anio_activo(
            cursor, estudiante_id
        )

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


def _anio_de_la_lista(cursor, anio_lectivo_id):
    """El año cuyas matriculas forman la lista, o `None` para la de siempre.

    Sin año, o con el activo, `None`: la lista de hoy, con todos los
    estudiantes. Con otro año, su id. Un año que no existe lanza `ValueError`.
    """
    if anio_lectivo_id is None:
        return None
    anio = exigir_anio_lectivo(cursor, anio_lectivo_id)
    return None if anio[2] == "activo" else anio_lectivo_id


# 🎯 Obtener todos los estudiantes
def obtener_estudiantes_controller(estado="activo", anio_lectivo_id=None):
    """Sin año, o con el activo, todos; con otro año, sus matriculados."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        estado_where, parametros = _build_estado_filter(estado)
        where_sql = f"WHERE {estado_where}" if estado_where else ""

        resultado = estudiantes_repository.listar_estudiantes(
            cursor, where_sql, parametros,
            anio_lectivo_id=_anio_de_la_lista(cursor, anio_lectivo_id),
        )
    finally:
        cursor.close()
        conn.close()

    return [_formatear_estudiante_lista(row) for row in resultado]


def obtener_estudiantes_paginado_controller(
    limit=50, offset=0, busqueda=None, estado="activo", anio_lectivo_id=None
):
    """Sin año, o con el activo, todos; con otro año, sus matriculados."""
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
        anio_de_la_lista = _anio_de_la_lista(cursor, anio_lectivo_id)
        total = estudiantes_repository.contar_estudiantes(
            cursor, where_sql, parametros, anio_lectivo_id=anio_de_la_lista
        )

        filas = estudiantes_repository.listar_estudiantes_paginado(
            cursor, where_sql, parametros + [limit, offset],
            anio_lectivo_id=anio_de_la_lista,
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_formatear_estudiante_lista(row) for row in filas],
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

        resultado = estudiantes_repository.actualizar_estudiante(cursor, (
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
        # Fase 1 del año lectivo: si cambio el curso, la matricula del año
        # activo lo sigue, en la misma transaccion.
        if resultado:
            anios_lectivos_repository.sincronizar_matricula_del_anio_activo(
                cursor, est_id
            )

    if resultado:
        return {"mensaje": "Estudiante actualizado correctamente", "id": resultado[0]}
    else:
        return {"mensaje": "Estudiante no encontrado"}

def obtener_estudiante_por_id_controller(est_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        row = estudiantes_repository.obtener_estudiante(cursor, est_id)
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
        row = estudiantes_repository.actualizar_estado_estudiante(
            cursor, estado_normalizado, est_id
        )
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


def obtener_deudas_estudiante_controller(est_id, anio_lectivo_id=None):
    """Deudas del estudiante en un año; sin `anio_lectivo_id`, en el activo.

    `deuda_anios_anteriores` trae aparte lo que debe de los años anteriores
    a ese (decision 2 del año lectivo); vacio mientras haya un solo año.
    """
    with get_cursor() as cursor:
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)
        resumen_cobros = calcular_deudas_estudiante(cursor, est_id, **con_anio(anio_lectivo_id))
        anteriores = calcular_deudas_anios_anteriores(
            cursor, (est_id,), **con_anio(anio_lectivo_id),
        )

    respuesta = _formatear_resumen_deudas(est_id, resumen_cobros)
    respuesta["deuda_anios_anteriores"] = anteriores.get(est_id, [])
    return respuesta


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
            filas_notas = estudiantes_repository.leer_promedios_por_materia(cursor, est_id)

            notas_list = [{'materia': r[0], 'promedio': float(r[1])} for r in filas_notas]
            detalles['notas'] = notas_list

            if notas_list:
                promedio_gen = sum(n['promedio'] for n in notas_list) / len(notas_list)
                detalles['promedio_general'] = round(promedio_gen, 1)
        except Exception as exc:
            conn.rollback()
            _registrar_error_detalle(detalles, "notas", exc)

        try:
            detalles['inasistencias'] = estudiantes_repository.contar_inasistencias(
                cursor, est_id
            )
        except Exception as exc:
            conn.rollback()
            _registrar_error_detalle(detalles, "asistencia", exc)

        try:
            filas_observaciones = estudiantes_repository.leer_observaciones(cursor, est_id)

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
                for r in filas_observaciones
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
            filas_inventario = estudiantes_repository.leer_cargos_de_inventario(
                cursor, est_id
            )

            productos_inventario = []
            for v_row in filas_inventario:
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




