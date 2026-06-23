from app.database import get_connection

ESTADOS_CURSO = {"activo", "inactivo"}
ESTADO_CURSO_DEFAULT = "activo"


def _title_case_es(value):
    return " ".join(
        word[:1].upper() + word[1:].lower()
        for word in str(value or "").strip().split()
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

    cursor.execute("""
        INSERT INTO cursos (nombre, jornada, estado)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (
        _title_case_es(curso.nombre),
        curso.jornada,
        _normalizar_estado(curso.estado),
    ))

    curso_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return curso_id 


def _formatear_curso(row):
    return {
        "id": row[0],
        "nombre": row[1],
        "jornada": row[2] or "Mañana",
        "estado": _normalizar_estado(row[3] if len(row) > 3 else ESTADO_CURSO_DEFAULT),
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
            SELECT id, nombre, jornada, COALESCE(LOWER(estado), 'activo') AS estado
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
            SELECT id, nombre, jornada, COALESCE(LOWER(estado), 'activo') AS estado
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
    from app.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE cursos
        SET nombre = %s, jornada = %s, estado = %s
        WHERE id = %s
    ''', (_title_case_es(curso.nombre), curso.jornada, _normalizar_estado(curso.estado), curso_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Curso actualizado correctamente"}


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
            RETURNING id, nombre, jornada, COALESCE(LOWER(estado), 'activo') AS estado
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
