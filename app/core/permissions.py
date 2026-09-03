from fastapi import HTTPException, status

from app.database import get_connection
from app.repositories.plan_de_clases_repository import (
    profesor_tiene_acceso_plan_de_clases_cursor,
)


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


def require_asignacion_access(
    asignacion_id: int,
    current_user: dict,
    detail: str = "No autorizado",
    *,
    cursor=None,
) -> None:
    if current_user.get("rol") == "admin":
        return

    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    if cursor is not None:
        cursor.execute(
            "SELECT 1 FROM asignaciones WHERE id = %s AND profesor_id = %s",
            (asignacion_id, current_user.get("id")),
        )
        if cursor.fetchone():
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    conn = get_connection()
    own_cursor = conn.cursor()
    try:
        own_cursor.execute(
            "SELECT 1 FROM asignaciones WHERE id = %s AND profesor_id = %s",
            (asignacion_id, current_user.get("id")),
        )
        if own_cursor.fetchone():
            return
    finally:
        own_cursor.close()
        conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


_SQL_ESTUDIANTE_EN_ASIGNACION = """
    SELECT 1
    FROM estudiantes e
    JOIN asignaciones a ON a.curso_id = e.curso_id
    WHERE e.id = %s AND a.id = %s
"""


def require_estudiante_in_asignacion(
    estudiante_id: int,
    asignacion_id: int,
    *,
    cursor=None,
) -> None:
    """Comprueba que el estudiante pertenece al curso de la asignacion.

    `cursor` es opcional y replica el que ya acepta `require_asignacion_access`:
    quien ya tiene una conexion abierta presta su cursor y se ahorra pedir otra
    al pool. Sin el, abre y cierra la suya, que es el comportamiento historico y
    el que siguen usando los llamadores que no tienen cursor a mano.

    Reutilizar el cursor **no relaja el permiso**: es la misma consulta con los
    mismos parametros, y el 403 se lanza igual.
    """
    if cursor is not None:
        cursor.execute(_SQL_ESTUDIANTE_EN_ASIGNACION, (estudiante_id, asignacion_id))
        if cursor.fetchone():
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El estudiante no pertenece a esta asignación",
        )

    conn = get_connection()
    own_cursor = conn.cursor()
    try:
        own_cursor.execute(
            _SQL_ESTUDIANTE_EN_ASIGNACION,
            (estudiante_id, asignacion_id),
        )
        if own_cursor.fetchone():
            return
    finally:
        own_cursor.close()
        conn.close()

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="El estudiante no pertenece a esta asignación",
    )


def require_estudiantes_in_asignacion(estudiante_ids: list[int], asignacion_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM estudiantes e
            JOIN asignaciones a ON a.curso_id = e.curso_id
            WHERE e.id = ANY(%s) AND a.id = %s
            """,
            (estudiante_ids, asignacion_id),
        )
        resultado = cursor.fetchone()
        if resultado and resultado[0] == len(estudiante_ids):
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
        if profesor_tiene_acceso_plan_de_clases_cursor(
            cursor,
            plan_id,
            current_user.get("id"),
        ):
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
