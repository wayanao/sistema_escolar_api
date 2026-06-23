from app.database import get_connection
from psycopg2 import IntegrityError

ESTADOS_MATERIA = {"activo", "inactivo"}
ESTADO_MATERIA_DEFAULT = "activo"


class MateriaDuplicadaError(Exception):
    """Se lanza cuando ya existe una materia con el mismo nombre."""


def _upper_text(value):
    return " ".join(str(value or "").strip().split()).upper()


def _validar_nombre_obligatorio(nombre):
    if not nombre:
        raise ValueError("El nombre de la materia es obligatorio.")


def _validar_materia_unica(cursor, nombre, materia_id=None):
    cursor.execute(
        """
        SELECT id
        FROM materias
        WHERE UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g')) = %s
          AND (%s IS NULL OR id <> %s)
        LIMIT 1
        """,
        (nombre, materia_id, materia_id),
    )
    if cursor.fetchone():
        raise MateriaDuplicadaError(f"Ya existe una materia llamada '{nombre}'.")


def _normalizar_estado(value):
    estado = str(value or ESTADO_MATERIA_DEFAULT).strip().lower()
    return estado if estado in ESTADOS_MATERIA else ESTADO_MATERIA_DEFAULT


def _agregar_filtro_estado(filtros, params, estado):
    estado_filtro = str(estado or ESTADO_MATERIA_DEFAULT).strip().lower()
    if estado_filtro == "todos":
        return

    filtros.append("COALESCE(LOWER(estado), 'activo') = %s")
    params.append(_normalizar_estado(estado_filtro))


def _formatear_materia(row):
    return {
        "id": row[0],
        "nombre": row[1],
        "estado": _normalizar_estado(row[2] if len(row) > 2 else ESTADO_MATERIA_DEFAULT),
    }


def crear_materia_controller(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        nombre = _upper_text(data.get("nombre"))
        _validar_nombre_obligatorio(nombre)
        _validar_materia_unica(cursor, nombre)

        cursor.execute("""
            INSERT INTO materias (nombre, estado)
            VALUES (%s, %s)
        """, (nombre, _normalizar_estado(data.get("estado"))))

        conn.commit()
        return {"mensaje": "Materia creada"}
    except (MateriaDuplicadaError, ValueError):
        conn.rollback()
        raise
    except IntegrityError as exc:
        conn.rollback()
        raise MateriaDuplicadaError(
            "Ya existe una materia con ese nombre."
        ) from exc
    finally:
        cursor.close()
        conn.close()



def obtener_materias_controller(estado=ESTADO_MATERIA_DEFAULT):

    conn = get_connection()
    cursor = conn.cursor()
    try:
        filtros = []
        params = []
        _agregar_filtro_estado(filtros, params, estado)
        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute("""
            SELECT id, nombre, COALESCE(LOWER(estado), 'activo') AS estado
            FROM materias
            {where_sql}
            ORDER BY id
        """.format(where_sql=where_sql), params)

        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return [_formatear_materia(r) for r in rows]

def obtener_materias_paginado_controller(limit=50, offset=0, busqueda=None, estado=ESTADO_MATERIA_DEFAULT):
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

        cursor.execute(f"SELECT COUNT(*) FROM materias {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, nombre, COALESCE(LOWER(estado), 'activo') AS estado
            FROM materias
            {where_sql}
            ORDER BY id
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        rows = cursor.fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_formatear_materia(r) for r in rows]
        }
    finally:
        cursor.close()
        conn.close()

def actualizar_materia_controller(materia_id, data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        nombre = _upper_text(data.get("nombre"))
        _validar_nombre_obligatorio(nombre)
        _validar_materia_unica(cursor, nombre, materia_id)

        cursor.execute('''
            UPDATE materias
            SET nombre = %s, estado = %s
            WHERE id = %s
            RETURNING id
        ''', (nombre, _normalizar_estado(data.get("estado")), materia_id))
        if not cursor.fetchone():
            conn.rollback()
            return {"error": "Materia no encontrada"}
        conn.commit()
        return {"mensaje": "Materia actualizada correctamente"}
    except (MateriaDuplicadaError, ValueError):
        conn.rollback()
        raise
    except IntegrityError as exc:
        conn.rollback()
        raise MateriaDuplicadaError(
            "Ya existe una materia con ese nombre."
        ) from exc
    finally:
        cursor.close()
        conn.close()


def actualizar_estado_materia_controller(materia_id, estado):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        estado_normalizado = _normalizar_estado(estado)
        cursor.execute(
            """
            UPDATE materias
            SET estado = %s
            WHERE id = %s
            RETURNING id, nombre, COALESCE(LOWER(estado), 'activo') AS estado
            """,
            (estado_normalizado, materia_id),
        )
        row = cursor.fetchone()
        if not row:
            return {"error": "Materia no encontrada"}

        conn.commit()
        return _formatear_materia(row)
    finally:
        cursor.close()
        conn.close()
