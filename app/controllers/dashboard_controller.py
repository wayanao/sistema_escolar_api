from app.database import get_connection, get_cursor
from app.repositories import dashboard_repository
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor


def _formatear_cumpleanos_estudiante(row):
    return {
        "estudiante_id": row[0],
        "nombre": row[1],
        "apellido": row[2],
        "curso": row[3],
        "fecha_nacimiento": str(row[4]) if row[4] else None,
    }


def _normalizar_dias_cumpleanos(dias):
    try:
        return max(0, min(int(dias), 31))
    except (TypeError, ValueError):
        return 7


def obtener_cumpleanos_admin_controller(dias=7):
    dias_normalizados = _normalizar_dias_cumpleanos(dias)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        filas = dashboard_repository.leer_cumpleanos_todos(cursor, dias_normalizados)
        return [_formatear_cumpleanos_estudiante(row) for row in filas]
    finally:
        cursor.close()
        conn.close()


def obtener_cumpleanos_profesor_controller(profesor_id, dias=7):
    dias_normalizados = _normalizar_dias_cumpleanos(dias)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        filas = dashboard_repository.leer_cumpleanos_de_profesor(
            cursor, dias_normalizados, profesor_id
        )
        return [_formatear_cumpleanos_estudiante(row) for row in filas]
    finally:
        cursor.close()
        conn.close()


def profesor_tiene_curso_controller(profesor_id, curso_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        fila = dashboard_repository.buscar_curso_de_profesor(cursor, profesor_id, curso_id)
        return fila is not None
    finally:
        cursor.close()
        conn.close()


def profesor_tiene_asignacion_en_curso_controller(profesor_id, curso_id, asignacion_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        fila = dashboard_repository.buscar_asignacion_de_profesor_en_curso(
            cursor, asignacion_id, profesor_id, curso_id
        )
        return fila is not None
    finally:
        cursor.close()
        conn.close()


def obtener_inasistencias_profesor_controller(profesor_id):
    with get_cursor() as cursor:
        resultados = dashboard_repository.leer_inasistencias_por_curso(cursor, profesor_id)

    return [
        {
            "curso_id": row[0],
            "curso": row[1],
            "estudiante_id": row[2],
            "nombre": row[3],
            "total_fallas": row[4],
            "posicion": row[5],
        }
        for row in resultados
    ]


def _obtener_notas_profesor(profesor_id, curso_id, asignacion_id=None, altas=False):
    with get_cursor() as cursor:
        if asignacion_id is not None:
            asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

        resultados = dashboard_repository.leer_estudiantes_por_promedio(
            cursor, profesor_id, curso_id, asignacion_id, altas
        )

    items = []
    for row in resultados:
        promedio = float(row[3])
        items.append({
            "nombre": row[0],
            "curso": row[1],
            "materia": row[2],
            "promedio": promedio,
            "color": "green" if altas else "red" if promedio < 3.0 else "yellow",
        })
    return items


def obtener_notas_bajas_profesor_controller(profesor_id, curso_id, asignacion_id=None):
    return _obtener_notas_profesor(profesor_id, curso_id=curso_id, asignacion_id=asignacion_id, altas=False)


def obtener_notas_altas_profesor_controller(profesor_id, curso_id, asignacion_id=None):
    return _obtener_notas_profesor(profesor_id, curso_id=curso_id, asignacion_id=asignacion_id, altas=True)


def obtener_ranking_rendimiento_controller(asignacion_id, periodo):
    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

        resultados = dashboard_repository.leer_ranking_bajo_rendimiento(
            cursor, asignacion_id, periodo
        )

    return [
        {"id": row[0], "nombre": row[1], "promedio": float(row[2])}
        for row in resultados
    ]


def obtener_ranking_mejor_rendimiento_controller(asignacion_id, periodo):
    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

        resultados = dashboard_repository.leer_ranking_mejor_rendimiento(
            cursor, asignacion_id, periodo
        )

    return [
        {"id": row[0], "nombre": row[1], "promedio": float(row[2])}
        for row in resultados
    ]
