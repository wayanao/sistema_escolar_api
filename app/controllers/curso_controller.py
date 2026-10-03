from app.database import get_connection
from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL, condicion_anio
from app.services.anio_lectivo import exigir_anio_lectivo, exigir_cursos_editables_para_admin
from psycopg2 import IntegrityError

ESTADOS_CURSO = {"activo", "inactivo"}
ESTADO_CURSO_DEFAULT = "activo"


class CursoDuplicadoError(Exception):
    """Se lanza cuando ya existe un curso con el mismo nombre y jornada."""


def _upper_text(value):
    return " ".join(str(value or "").strip().split()).upper()


def _normalizar_jornada(value):
    return str(value or "Mañana").strip() or "Mañana"


def _validar_nombre_obligatorio(nombre):
    if not nombre:
        raise ValueError("El nombre del curso es obligatorio.")


def _validar_curso_unico(cursor, nombre, jornada, curso_id=None):
    # Fase 3 del año lectivo: el nombre se repite una vez por año, como el
    # indice unico de la migracion A. Un curso nuevo nace en el año activo; uno
    # que se edita se compara con los de su propio año. Sin esto, copiar los
    # cursos a 2027 (fase 5) fallaria como "repetido".
    if curso_id is None:
        anio_sql, params_anio = ANIO_ACTIVO_ID_SQL, ()
    else:
        anio_sql = "(SELECT anio_lectivo_id FROM cursos WHERE id = %s)"
        params_anio = (curso_id,)
    cursor.execute(
        f"""
        SELECT id
        FROM cursos
        WHERE UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g')) = %s
          AND LOWER(COALESCE(NULLIF(TRIM(jornada), ''), 'Mañana')) =
              LOWER(COALESCE(NULLIF(TRIM(%s), ''), 'Mañana'))
          AND (%s IS NULL OR id <> %s)
          AND anio_lectivo_id = {anio_sql}
        LIMIT 1
        """,
        (nombre, jornada, curso_id, curso_id, *params_anio),
    )
    if cursor.fetchone():
        raise CursoDuplicadoError(
            f"Ya existe un curso llamado '{nombre}' en la jornada {jornada}."
        )


def _normalizar_estado(value):
    estado = str(value or ESTADO_CURSO_DEFAULT).strip().lower()
    return estado if estado in ESTADOS_CURSO else ESTADO_CURSO_DEFAULT


def _agregar_filtro_estado(filtros, params, estado):
    estado_filtro = str(estado or ESTADO_CURSO_DEFAULT).strip().lower()
    if estado_filtro == "todos":
        return

    filtros.append("COALESCE(LOWER(estado), 'activo') = %s")
    params.append(_normalizar_estado(estado_filtro))


def _agregar_filtro_anio(filtros, params, anio_lectivo_id):
    # Fase 3 del año lectivo: solo los cursos de un año. Sin año, el activo y
    # ningun parametro nuevo. Va el ultimo, despues de busqueda y estado.
    condicion, params_anio = condicion_anio("anio_lectivo_id", anio_lectivo_id)
    filtros.append(condicion)
    params.extend(params_anio)


# 🎯 Crear curso
def crear_curso_controller(curso):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        nombre = _upper_text(curso.nombre)
        jornada = _normalizar_jornada(curso.jornada)
        _validar_nombre_obligatorio(nombre)
        _validar_curso_unico(cursor, nombre, jornada)

        # Fase 1 del año lectivo: el curso nace en el año activo.
        cursor.execute(f"""
            INSERT INTO cursos (nombre, jornada, estado, nivel, director_grupo_id, anio_lectivo_id)
            VALUES (%s, %s, %s, %s, %s, {ANIO_ACTIVO_ID_SQL})
            RETURNING id
        """, (
            nombre,
            jornada,
            _normalizar_estado(curso.estado),
            curso.nivel,
            curso.director_grupo_id,
        ))

        curso_id = cursor.fetchone()[0]

        conn.commit()
        return curso_id
    except (CursoDuplicadoError, ValueError):
        conn.rollback()
        raise
    except IntegrityError as exc:
        conn.rollback()
        raise CursoDuplicadoError(
            "Ya existe un curso con ese nombre y jornada."
        ) from exc
    finally:
        cursor.close()
        conn.close()


def _formatear_curso(row):
    return {
        "id": row[0],
        "nombre": row[1],
        "jornada": row[2] or "Mañana",
        "estado": _normalizar_estado(row[3] if len(row) > 3 else ESTADO_CURSO_DEFAULT),
        "nivel": row[4] if len(row) > 4 else None,
        "director_grupo_id": row[5] if len(row) > 5 else None,
    }


# 🎯 Listar cursos
def obtener_cursos_controller(estado=ESTADO_CURSO_DEFAULT, anio_lectivo_id=None):
    """Cursos de un año; sin `anio_lectivo_id`, del activo."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)

        filtros = []
        params = []
        _agregar_filtro_estado(filtros, params, estado)
        _agregar_filtro_anio(filtros, params, anio_lectivo_id)
        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute("""
            SELECT id, nombre, jornada, COALESCE(LOWER(estado), 'activo') AS estado, nivel, director_grupo_id
            FROM cursos
            {where_sql}
            ORDER BY id
        """.format(where_sql=where_sql), params)

        resultado = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return [_formatear_curso(row) for row in resultado]

def obtener_cursos_paginado_controller(
    limit=50, offset=0, busqueda=None, estado=ESTADO_CURSO_DEFAULT, anio_lectivo_id=None
):
    """Pagina de cursos de un año; sin `anio_lectivo_id`, del activo."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)

        filtros = []
        params = []

        if busqueda:
            filtros.append("LOWER(nombre) LIKE LOWER(%s)")
            params.append(f"%{busqueda}%")

        _agregar_filtro_estado(filtros, params, estado)
        _agregar_filtro_anio(filtros, params, anio_lectivo_id)

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"SELECT COUNT(*) FROM cursos {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, nombre, jornada, COALESCE(LOWER(estado), 'activo') AS estado, nivel, director_grupo_id
            FROM cursos
            {where_sql}
            ORDER BY id
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        resultado = cursor.fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_formatear_curso(row) for row in resultado]
        }
    finally:
        cursor.close()
        conn.close()

def actualizar_curso_controller(curso_id, curso):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        nombre = _upper_text(curso.nombre)
        jornada = _normalizar_jornada(curso.jornada)
        _validar_nombre_obligatorio(nombre)
        # Año lectivo, paso 3.7: antes de la primera consulta, en la conexion
        # que ya se abrio.
        exigir_cursos_editables_para_admin(cursor, [curso_id])
        _validar_curso_unico(cursor, nombre, jornada, curso_id)

        cursor.execute('''
            UPDATE cursos
            SET nombre = %s, jornada = %s, estado = %s, nivel = %s, director_grupo_id = %s
            WHERE id = %s
            RETURNING id
        ''', (
            nombre,
            jornada,
            _normalizar_estado(curso.estado),
            curso.nivel,
            curso.director_grupo_id,
            curso_id,
        ))
        if not cursor.fetchone():
            conn.rollback()
            return {"error": "Curso no encontrado"}
        conn.commit()
        return {"mensaje": "Curso actualizado correctamente"}
    except (CursoDuplicadoError, ValueError):
        conn.rollback()
        raise
    except IntegrityError as exc:
        conn.rollback()
        raise CursoDuplicadoError(
            "Ya existe un curso con ese nombre y jornada."
        ) from exc
    finally:
        cursor.close()
        conn.close()


def actualizar_estado_curso_controller(curso_id, estado):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_cursos_editables_para_admin(cursor, [curso_id])
        estado_normalizado = _normalizar_estado(estado)
        cursor.execute(
            """
            UPDATE cursos
            SET estado = %s
            WHERE id = %s
            RETURNING id, nombre, jornada, COALESCE(LOWER(estado), 'activo') AS estado, nivel, director_grupo_id
            """,
            (estado_normalizado, curso_id),
        )
        row = cursor.fetchone()
        if not row:
            return {"error": "Curso no encontrado"}

        conn.commit()
        return _formatear_curso(row)
    finally:
        cursor.close()
        conn.close()
