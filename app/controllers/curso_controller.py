from app.database import get_connection
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
    cursor.execute(
        """
        SELECT id
        FROM cursos
        WHERE UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g')) = %s
          AND LOWER(COALESCE(NULLIF(TRIM(jornada), ''), 'Mañana')) =
              LOWER(COALESCE(NULLIF(TRIM(%s), ''), 'Mañana'))
          AND (%s IS NULL OR id <> %s)
        LIMIT 1
        """,
        (nombre, jornada, curso_id, curso_id),
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


# 🎯 Crear curso
def crear_curso_controller(curso):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        nombre = _upper_text(curso.nombre)
        jornada = _normalizar_jornada(curso.jornada)
        _validar_nombre_obligatorio(nombre)
        _validar_curso_unico(cursor, nombre, jornada)

        cursor.execute("""
            INSERT INTO cursos (nombre, jornada, estado, nivel)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            nombre,
            jornada,
            _normalizar_estado(curso.estado),
            curso.nivel,
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
    }


# 🎯 Listar cursos
def obtener_cursos_controller(estado=ESTADO_CURSO_DEFAULT):

    conn = get_connection()
    cursor = conn.cursor()
    try:
        filtros = []
        params = []
        _agregar_filtro_estado(filtros, params, estado)
        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute("""
            SELECT id, nombre, jornada, COALESCE(LOWER(estado), 'activo') AS estado, nivel
            FROM cursos
            {where_sql}
            ORDER BY id
        """.format(where_sql=where_sql), params)

        resultado = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return [_formatear_curso(row) for row in resultado]

def obtener_cursos_paginado_controller(limit=50, offset=0, busqueda=None, estado=ESTADO_CURSO_DEFAULT):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        filtros = []
        params = []

        if busqueda:
            filtros.append("LOWER(nombre) LIKE LOWER(%s)")
            params.append(f"%{busqueda}%")

        _agregar_filtro_estado(filtros, params, estado)

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"SELECT COUNT(*) FROM cursos {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, nombre, jornada, COALESCE(LOWER(estado), 'activo') AS estado, nivel
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
        _validar_curso_unico(cursor, nombre, jornada, curso_id)

        cursor.execute('''
            UPDATE cursos
            SET nombre = %s, jornada = %s, estado = %s, nivel = %s
            WHERE id = %s
            RETURNING id
        ''', (nombre, jornada, _normalizar_estado(curso.estado), curso.nivel, curso_id))
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
        estado_normalizado = _normalizar_estado(estado)
        cursor.execute(
            """
            UPDATE cursos
            SET estado = %s
            WHERE id = %s
            RETURNING id, nombre, jornada, COALESCE(LOWER(estado), 'activo') AS estado, nivel
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
