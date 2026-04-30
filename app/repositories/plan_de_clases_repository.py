from app.database import get_cursor


PLAN_SELECT = """
    SELECT
        pdc.id,
        pdc.asignacion_id,
        COALESCE(pdc.periodo, 1) AS periodo,
        pdc.unidad,
        pdc.proposito,
        COALESCE(pdc.clase, '') AS clase,
        pdc.estandar,
        pdc.dba,
        pdc.competencias,
        COALESCE(pdc.actividad_casa, '') AS actividad_casa,
        pdc.tema,
        pdc.fecha,
        pdc.imagen1,
        pdc.imagen2,
        a.profesor_id,
        CONCAT(pr.nombre, ' ', pr.apellido) AS profesor,
        c.nombre AS curso,
        m.nombre AS materia,
        pdc.created_at,
        pdc.updated_at
    FROM plan_de_clases pdc
    JOIN asignaciones a ON pdc.asignacion_id = a.id
    JOIN profesor pr ON a.profesor_id = pr.id
    JOIN cursos c ON a.curso_id = c.id
    JOIN materias m ON a.materia_id = m.id
"""


def _row_to_plan(row):
    return {
        "id": row[0],
        "asignacion_id": row[1],
        "periodo": row[2],
        "unidad": row[3],
        "proposito": row[4],
        "clase": row[5],
        "estandar": row[6],
        "dba": row[7],
        "competencias": row[8],
        "actividad_casa": row[9],
        "tema": row[10],
        "fecha": row[11],
        "imagen1": row[12],
        "imagen2": row[13],
        "profesor_id": row[14],
        "profesor": row[15],
        "curso": row[16],
        "materia": row[17],
        "created_at": row[18],
        "updated_at": row[19],
    }


def guardar_plan_de_clases(plan, imagen1_path=None, imagen2_path=None):
    with get_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE plan_de_clases
            SET
                periodo = %s,
                unidad = %s,
                proposito = %s,
                clase = %s,
                estandar = %s,
                dba = %s,
                competencias = %s,
                actividad_casa = %s,
                tema = %s,
                imagen1 = COALESCE(%s, imagen1),
                imagen2 = COALESCE(%s, imagen2),
                updated_at = CURRENT_TIMESTAMP
            WHERE asignacion_id = %s AND fecha = %s
            RETURNING id
            """,
            (
                plan.periodo,
                plan.unidad,
                plan.proposito,
                plan.clase,
                plan.estandar,
                plan.dba,
                plan.competencias,
                plan.actividad_casa,
                plan.tema,
                imagen1_path,
                imagen2_path,
                plan.asignacion_id,
                plan.fecha,
            ),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute(
            """
            INSERT INTO plan_de_clases (
                asignacion_id, periodo, unidad, proposito, clase, estandar,
                dba, competencias, actividad_casa, tema, fecha, imagen1, imagen2
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                plan.asignacion_id,
                plan.periodo,
                plan.unidad,
                plan.proposito,
                plan.clase,
                plan.estandar,
                plan.dba,
                plan.competencias,
                plan.actividad_casa,
                plan.tema,
                plan.fecha,
                imagen1_path,
                imagen2_path,
            ),
        )
        return cursor.fetchone()[0]


def obtener_plan_por_dia(asignacion_id, fecha):
    with get_cursor() as cursor:
        cursor.execute(
            PLAN_SELECT
            + """
            WHERE pdc.asignacion_id = %s AND pdc.fecha = %s
            """,
            (asignacion_id, fecha),
        )
        row = cursor.fetchone()
        return _row_to_plan(row) if row else None


def obtener_planes_por_asignacion(asignacion_id):
    with get_cursor() as cursor:
        cursor.execute(
            PLAN_SELECT
            + """
            WHERE pdc.asignacion_id = %s
            ORDER BY pdc.fecha DESC, pdc.created_at DESC
            """,
            (asignacion_id,),
        )
        return [_row_to_plan(row) for row in cursor.fetchall()]


def listar_planes_admin(
    profesor_id=None,
    fecha_desde=None,
    fecha_hasta=None,
    busqueda=None,
    limit=50,
    offset=0,
):
    condiciones = []
    parametros = []

    if profesor_id:
        condiciones.append("a.profesor_id = %s")
        parametros.append(profesor_id)
    if fecha_desde:
        condiciones.append("pdc.fecha >= %s")
        parametros.append(fecha_desde)
    if fecha_hasta:
        condiciones.append("pdc.fecha <= %s")
        parametros.append(fecha_hasta)
    if busqueda:
        condiciones.append(
            """
            (
                pdc.tema ILIKE %s OR
                pdc.unidad ILIKE %s OR
                CONCAT(pr.nombre, ' ', pr.apellido) ILIKE %s OR
                c.nombre ILIKE %s OR
                m.nombre ILIKE %s
            )
            """
        )
        like = f"%{busqueda}%"
        parametros.extend([like, like, like, like, like])

    where_sql = " WHERE " + " AND ".join(condiciones) if condiciones else ""

    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM plan_de_clases pdc
            JOIN asignaciones a ON pdc.asignacion_id = a.id
            JOIN profesor pr ON a.profesor_id = pr.id
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            """
            + where_sql,
            tuple(parametros),
        )
        total = cursor.fetchone()[0]

        cursor.execute(
            PLAN_SELECT
            + where_sql
            + """
            ORDER BY pdc.fecha DESC, pdc.created_at DESC
            LIMIT %s OFFSET %s
            """,
            tuple(parametros + [limit, offset]),
        )
        return {"total": total, "items": [_row_to_plan(row) for row in cursor.fetchall()]}
