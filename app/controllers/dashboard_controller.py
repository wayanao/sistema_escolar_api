from app.database import get_connection
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


def _cte_rango_cumpleanos():
    return """
        WITH parametros AS (
            SELECT
                (NOW() AT TIME ZONE 'America/Bogota')::date AS hoy,
                ((NOW() AT TIME ZONE 'America/Bogota')::date + %s) AS fecha_fin
        ),
        rango AS (
            SELECT
                hoy,
                fecha_fin,
                TO_CHAR(hoy, 'MMDD') AS inicio_mmdd,
                TO_CHAR(fecha_fin, 'MMDD') AS fin_mmdd
            FROM parametros
        )
    """


def _filtro_rango_cumpleanos(alias_estudiante="e"):
    return f"""
        AND (
            (
                r.inicio_mmdd <= r.fin_mmdd
                AND TO_CHAR({alias_estudiante}.fecha_nacimiento, 'MMDD') BETWEEN r.inicio_mmdd AND r.fin_mmdd
            )
            OR (
                r.inicio_mmdd > r.fin_mmdd
                AND (
                    TO_CHAR({alias_estudiante}.fecha_nacimiento, 'MMDD') >= r.inicio_mmdd
                    OR TO_CHAR({alias_estudiante}.fecha_nacimiento, 'MMDD') <= r.fin_mmdd
                )
            )
        )
    """


def obtener_cumpleanos_admin_controller(dias=7):
    dias_normalizados = _normalizar_dias_cumpleanos(dias)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            _cte_rango_cumpleanos()
            + """
            SELECT
                e.id,
                e.nombre,
                e.apellido,
                c.nombre AS curso,
                e.fecha_nacimiento
            FROM estudiantes e
            LEFT JOIN cursos c ON e.curso_id = c.id
            CROSS JOIN rango r
            WHERE e.fecha_nacimiento IS NOT NULL
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
            """
            + _filtro_rango_cumpleanos()
            + """
            ORDER BY
                CASE WHEN TO_CHAR(e.fecha_nacimiento, 'MMDD') >= r.inicio_mmdd THEN 0 ELSE 1 END,
                TO_CHAR(e.fecha_nacimiento, 'MMDD') ASC,
                c.nombre ASC NULLS LAST,
                e.apellido ASC,
                e.nombre ASC
            """,
            (dias_normalizados,),
        )
        return [_formatear_cumpleanos_estudiante(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def obtener_cumpleanos_profesor_controller(profesor_id, dias=7):
    dias_normalizados = _normalizar_dias_cumpleanos(dias)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            _cte_rango_cumpleanos()
            + """
            SELECT
                e.id,
                e.nombre,
                e.apellido,
                c.nombre AS curso,
                e.fecha_nacimiento
            FROM estudiantes e
            JOIN cursos c ON e.curso_id = c.id
            CROSS JOIN rango r
            WHERE EXISTS (
                SELECT 1
                FROM asignaciones a
                WHERE a.curso_id = c.id
                  AND a.profesor_id = %s
                  AND a.activo = TRUE
            )
              AND e.fecha_nacimiento IS NOT NULL
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
              AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
            """
            + _filtro_rango_cumpleanos()
            + """
            ORDER BY
                CASE WHEN TO_CHAR(e.fecha_nacimiento, 'MMDD') >= r.inicio_mmdd THEN 0 ELSE 1 END,
                TO_CHAR(e.fecha_nacimiento, 'MMDD') ASC,
                c.nombre ASC,
                e.apellido ASC,
                e.nombre ASC
            """,
            (dias_normalizados, profesor_id),
        )
        return [_formatear_cumpleanos_estudiante(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def profesor_tiene_curso_controller(profesor_id, curso_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 1
            FROM asignaciones
            WHERE profesor_id = %s AND curso_id = %s
            LIMIT 1
            """,
            (profesor_id, curso_id),
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


def profesor_tiene_asignacion_en_curso_controller(profesor_id, curso_id, asignacion_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        cursor.execute(
            """
            SELECT 1
            FROM asignaciones
            WHERE id = %s AND profesor_id = %s AND curso_id = %s
            LIMIT 1
            """,
            (asignacion_id, profesor_id, curso_id),
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


def obtener_inasistencias_profesor_controller(profesor_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        WITH conteos AS (
            SELECT
                c.id as curso_id,
                c.nombre as curso,
                e.id as estudiante_id,
                e.nombre || ' ' || e.apellido as nombre_estudiante,
                COUNT(a.id) as total_fallas,
                ROW_NUMBER() OVER (
                    PARTITION BY c.id
                    ORDER BY COUNT(a.id) DESC, e.apellido ASC, e.nombre ASC
                ) as posicion_curso
            FROM asistencia a
            JOIN estudiantes e ON a.estudiante_id = e.id
            JOIN asignaciones asi ON a.asignacion_id = asi.id
            JOIN cursos c ON asi.curso_id = c.id
            WHERE asi.profesor_id = %s AND a.estado ILIKE 'ausente'
            GROUP BY c.id, c.nombre, e.id, e.nombre, e.apellido
        )
        SELECT curso_id, curso, estudiante_id, nombre_estudiante, total_fallas, posicion_curso
        FROM conteos
        WHERE posicion_curso <= 3
        ORDER BY curso ASC, posicion_curso ASC, total_fallas DESC
    """, (profesor_id,))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

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
    conn = get_connection()
    cursor = conn.cursor()

    if asignacion_id is not None:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

    filtro_asignacion = "AND asi.id = %s" if asignacion_id is not None else ""
    params = [profesor_id, curso_id]
    if asignacion_id is not None:
        params.append(asignacion_id)

    comparador = ">= 3.0" if altas else "< 3.0"
    orden = "DESC" if altas else "ASC"

    cursor.execute(f"""
        WITH PromediosPorClase AS (
            SELECT
                e.id as estudiante_id,
                e.nombre,
                e.apellido,
                c.nombre as curso,
                m.nombre as materia,
                AVG(CAST(n.nota AS numeric)) as promedio_clase
            FROM notas_detalle n
            JOIN estudiantes e ON n.estudiante_id = e.id
            JOIN asignaciones asi ON n.asignacion_id = asi.id
            JOIN cursos c ON asi.curso_id = c.id
            JOIN materias m ON asi.materia_id = m.id
            WHERE asi.profesor_id = %s
              AND asi.curso_id = %s
              AND n.nota IS NOT NULL
              {filtro_asignacion}
            GROUP BY e.id, e.nombre, e.apellido, c.nombre, m.nombre, asi.id
        )
        SELECT
            nombre || ' ' || apellido as nombre_estudiante,
            MAX(curso) as curso,
            CASE WHEN %s IS NULL THEN 'Todas las materias' ELSE MAX(materia) END as materia,
            TRUNC(AVG(promedio_clase), 2) as promedio
        FROM PromediosPorClase
        GROUP BY estudiante_id, nombre, apellido
        HAVING TRUNC(AVG(promedio_clase), 2) {comparador}
        ORDER BY promedio {orden}, nombre ASC, apellido ASC
        LIMIT 5
    """, (*params, asignacion_id))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

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
    conn = get_connection()
    cursor = conn.cursor()
    asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

    cursor.execute("""
        SELECT
            e.id as estudiante_id,
            e.nombre || ' ' || e.apellido as nombre_estudiante,
            TRUNC(AVG(CAST(n.nota AS numeric)), 2) as promedio
        FROM notas_detalle n
        JOIN estudiantes e ON n.estudiante_id = e.id
        WHERE n.asignacion_id = %s AND n.periodo = %s
        GROUP BY e.id, e.nombre, e.apellido
        HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) < 3.0
        ORDER BY promedio ASC
    """, (asignacion_id, periodo))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {"id": row[0], "nombre": row[1], "promedio": float(row[2])}
        for row in resultados
    ]


def obtener_ranking_mejor_rendimiento_controller(asignacion_id, periodo):
    conn = get_connection()
    cursor = conn.cursor()
    asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

    cursor.execute("""
        SELECT
            e.id as estudiante_id,
            e.nombre || ' ' || e.apellido as nombre_estudiante,
            TRUNC(AVG(CAST(n.nota AS numeric)), 2) as promedio
        FROM notas_detalle n
        JOIN estudiantes e ON n.estudiante_id = e.id
        WHERE n.asignacion_id = %s AND n.periodo = %s
        GROUP BY e.id, e.nombre, e.apellido
        HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) >= 3.0
        ORDER BY promedio DESC
    """, (asignacion_id, periodo))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {"id": row[0], "nombre": row[1], "promedio": float(row[2])}
        for row in resultados
    ]
