from fastapi import HTTPException, status

from app.database import get_connection


def require_estudiante_access(estudiante_id: int, current_user: dict) -> None:
    if current_user.get("rol") == "admin":
        return

    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 1
            FROM estudiantes e
            JOIN asignaciones a ON a.curso_id = e.curso_id
            WHERE e.id = %s AND a.profesor_id = %s
            """,
            (estudiante_id, current_user.get("id")),
        )
        if cursor.fetchone():
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
