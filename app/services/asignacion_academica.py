from app.database import get_connection


def resolver_asignacion_academica_id_cursor(cursor, asignacion_id):
    cursor.execute(
        """
        SELECT
            CASE
                WHEN base.id IS NOT NULL
                 AND base.profesor_id = a.profesor_id
                 AND base.curso_id = a.curso_id
                 AND base.materia_id = a.materia_id
                    THEN base.id
                ELSE a.id
            END AS asignacion_academica_id
        FROM asignaciones a
        LEFT JOIN asignaciones base ON base.id = a.asignacion_academica_id
        WHERE a.id = %s
        """,
        (asignacion_id,),
    )
    row = cursor.fetchone()
    if not row:
        return asignacion_id
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]


def resolver_asignacion_academica_id(asignacion_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        return resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
    finally:
        cursor.close()
        conn.close()


def resolver_nivel_curso_cursor(cursor, asignacion_id):
    """Nivel academico (preescolar/primaria) del curso de una asignacion.

    Devuelve None si la asignacion no existe o si su curso no tiene nivel
    definido: un curso sin nivel no fuerza ninguna regla, igual que el
    comportamiento anterior a la funcionalidad de nivel academico.
    """
    cursor.execute(
        """
        SELECT c.nivel
        FROM asignaciones a
        JOIN cursos c ON c.id = a.curso_id
        WHERE a.id = %s
        """,
        (asignacion_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]

