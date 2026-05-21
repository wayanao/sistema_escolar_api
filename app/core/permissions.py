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


def require_profesor_scope(profesor_id: int, current_user: dict, detail: str = "No autorizado") -> None:
    if current_user.get("rol") == "admin":
        return

    if current_user.get("rol") == "profesor" and current_user.get("id") == profesor_id:
        return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def require_asignacion_access(asignacion_id: int, current_user: dict, detail: str = "No autorizado") -> None:
    if current_user.get("rol") == "admin":
        return

    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM asignaciones WHERE id = %s AND profesor_id = %s",
            (asignacion_id, current_user.get("id")),
        )
        if cursor.fetchone():
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def require_estudiante_in_asignacion(estudiante_id: int, asignacion_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 1
            FROM estudiantes e
            JOIN asignaciones a ON a.curso_id = e.curso_id
            WHERE e.id = %s AND a.id = %s
            """,
            (estudiante_id, asignacion_id),
        )
        if cursor.fetchone():
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="El estudiante no pertenece a esta asignación",
    )


def require_plan_de_clases_access(plan_id: int, current_user: dict, detail: str = "No autorizado") -> None:
    if current_user.get("rol") == "admin":
        return

    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 1
            FROM plan_de_clases pdc
            JOIN asignaciones a ON pdc.asignacion_id = a.id
            WHERE pdc.id = %s AND a.profesor_id = %s
            """,
            (plan_id, current_user.get("id")),
        )
        if cursor.fetchone():
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
