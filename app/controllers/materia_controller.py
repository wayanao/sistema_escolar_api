from app.database import get_connection

ESTADOS_MATERIA = {"activo", "inactivo"}
ESTADO_MATERIA_DEFAULT = "activo"


def _upper_text(value):
    return " ".join(str(value or "").strip().split()).upper()


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

    cursor.execute("""
        INSERT INTO materias (nombre, estado)
        VALUES (%s, %s)
    """, (_upper_text(data["nombre"]), _normalizar_estado(data.get("estado"))))

    conn.commit()

    cursor.close()
    conn.close()

    return {"mensaje": "Materia creada"}



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
    from app.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE materias
        SET nombre = %s, estado = %s
        WHERE id = %s
    ''', (_upper_text(data["nombre"]), _normalizar_estado(data.get("estado")), materia_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Materia actualizada correctamente"}


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
