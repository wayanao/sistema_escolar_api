from app.database import get_connection


def resolver_asignacion_academica_id_cursor(cursor, asignacion_id):
    cursor.execute(
        """
        SELECT COALESCE(asignacion_academica_id, id)
        FROM asignaciones
        WHERE id = %s
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
