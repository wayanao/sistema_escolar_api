from fastapi import HTTPException, status

from app.database import get_connection
from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL
from app.repositories.plan_de_clases_repository import (
    profesor_tiene_acceso_plan_de_clases_cursor,
)


_SQL_PROFESOR_COMPARTE_CURSO = """
            SELECT 1
            FROM estudiantes e
            JOIN asignaciones a ON a.curso_id = e.curso_id
            WHERE e.id = %s AND a.profesor_id = %s
            """


def require_estudiante_access(
    estudiante_id: int,
    current_user: dict,
    *,
    cursor=None,
) -> None:
    """El profesor comparte curso con el estudiante, o es admin.

    `cursor` es opcional y replica el que ya aceptan `require_asignacion_access`
    y `require_estudiante_in_asignacion` desde el 2026-09-03: quien ya tiene una
    conexion abierta presta su cursor y se ahorra pedir otra al pool. Contra Neon
    cada ida y vuelta cuesta ~180 ms, y lo que se paga es el numero de idas y
    vueltas, no lo que consulte cada una. Sin `cursor` abre y cierra la suya, que
    es el comportamiento historico y el de los llamadores de `app/routes/notas.py`.

    Prestar el cursor **no relaja el permiso**: es la misma consulta con los
    mismos parametros, y el 403 se lanza igual.

    El atajo de admin de la primera linea es correcto **para leer**. En la
    edicion de una anotacion del observador NO debe copiarse: ver el invariante 3
    de `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`.
    """
    if current_user.get("rol") == "admin":
        return

    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    parametros = (estudiante_id, current_user.get("id"))

    if cursor is not None:
        cursor.execute(_SQL_PROFESOR_COMPARTE_CURSO, parametros)
        if cursor.fetchone():
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    conn = get_connection()
    own_cursor = conn.cursor()
    try:
        own_cursor.execute(_SQL_PROFESOR_COMPARTE_CURSO, parametros)
        if own_cursor.fetchone():
            return
    finally:
        own_cursor.close()
        conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


# "Mi curso" del director de grupo (docs/funcionalidades/MI_CURSO_DIRECTOR.md):
# el profesor dirige ese curso **del año activo**. Dar clase en el curso no
# basta: el director ve las notas de todos los profesores del curso.
_SQL_PROFESOR_DIRIGE_CURSO = f"""
    SELECT 1
    FROM cursos c
    WHERE c.id = %s
      AND c.director_grupo_id = %s
      AND c.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
"""


def require_director_de_curso(
    curso_id: int,
    current_user: dict,
    *,
    cursor=None,
) -> None:
    """El admin, o el profesor que es director de grupo de ese curso.

    Un profesor que solo da clase en el curso recibe **403**: este permiso abre
    las notas de las demás materias, que `require_asignacion_access` no abre.
    Un curso que no existe también da 403, para no revelar cuáles existen.

    `cursor` es opcional, como en `require_asignacion_access`: prestarlo ahorra
    pedir otra conexión al pool y no relaja el permiso.
    """
    if current_user.get("rol") == "admin":
        return

    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    parametros = (curso_id, current_user.get("id"))

    if cursor is not None:
        cursor.execute(_SQL_PROFESOR_DIRIGE_CURSO, parametros)
        if cursor.fetchone():
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    conn = get_connection()
    own_cursor = conn.cursor()
    try:
        own_cursor.execute(_SQL_PROFESOR_DIRIGE_CURSO, parametros)
        if own_cursor.fetchone():
            return
    finally:
        own_cursor.close()
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
