from app.database import get_connection
from app.security import get_password_hash

ESTADOS_PROFESOR = {"activo", "inactivo"}
ESTADOS_FILTRO_PROFESOR = ESTADOS_PROFESOR | {"todos"}


def normalizar_estado_profesor(estado, default="activo"):
    valor = str(estado or default).strip().lower()
    if valor not in ESTADOS_PROFESOR:
        raise ValueError("Estado de profesor invalido")
    return valor


def _build_estado_filter(estado):
    estado_normalizado = str(estado or "activo").strip().lower()
    if estado_normalizado not in ESTADOS_FILTRO_PROFESOR:
        raise ValueError("Filtro de estado de profesor invalido")
    if estado_normalizado == "todos":
        return "", []
    return "COALESCE(LOWER(estado), 'activo') = %s", [estado_normalizado]


def _title_case_es(value):
    return " ".join(
        word[:1].upper() + word[1:].lower()
        for word in str(value or "").strip().split()
    )


# 🎯 Crear profesor
def crear_profesor_controller(profesor):

    # 🔌 Abrimos conexión
    conn = get_connection()
    cursor = conn.cursor()
    estado = normalizar_estado_profesor(getattr(profesor, "estado", None))

    # 🧠 Insertamos en la base de datos (AGREGAMOS EMAIL)
    cursor.execute("""
        INSERT INTO profesor (
            nombre,
            apellido,
            documento_identidad,
            email,
            telefono,
            password,
            sueldo,
            estado
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        _title_case_es(profesor.nombre),
        _title_case_es(profesor.apellido),
        profesor.documento_identidad,
        str(profesor.email).strip().lower(),
        profesor.telefono,
        get_password_hash(profesor.password),
        profesor.sueldo,
        estado
    ))
    # 📥 Obtener ID
    profesor_id = cursor.fetchone()[0]

    # 💾 Guardar cambios
    conn.commit()

    # 🔒 Cerrar conexión
    cursor.close()
    conn.close()

    return profesor_id


# 🎯 Obtener todos los profesores
def obtener_profesores_controller(estado="activo"):

    conn = get_connection()
    cursor = conn.cursor()
    try:
        estado_where, params = _build_estado_filter(estado)
        where_sql = f"WHERE {estado_where}" if estado_where else ""

        cursor.execute(f"""
            SELECT
                id,
                nombre,
                apellido,
                documento_identidad,
                email,
                telefono,
                sueldo,
                COALESCE(LOWER(estado), 'activo') AS estado
            FROM profesor
            {where_sql}
            ORDER BY id
        """, params)

        resultado = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    data = []

    for row in resultado:
        data.append({
            "id": row[0],
            "nombre": row[1],
            "apellido": row[2],
            "documento": row[3],
            "email": row[4],
            "telefono": row[5],
            "sueldo": row[6],
            "estado": row[7]
        })

    return data

def obtener_profesores_paginado_controller(limit=50, offset=0, busqueda=None, estado="activo"):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        filtros = []
        params = []
        estado_where, estado_params = _build_estado_filter(estado)
        if estado_where:
            filtros.append(estado_where)
            params.extend(estado_params)

        if busqueda:
            filtros.append("""(
                LOWER(nombre || ' ' || apellido) LIKE LOWER(%s)
                OR LOWER(COALESCE(email, '')) LIKE LOWER(%s)
                OR LOWER(COALESCE(documento_identidad, '')) LIKE LOWER(%s)
            )""")
            patron = f"%{busqueda}%"
            params.extend([patron, patron, patron])

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"SELECT COUNT(*) FROM profesor {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT
                id,
                nombre,
                apellido,
                documento_identidad,
                email,
                telefono,
                sueldo,
                COALESCE(LOWER(estado), 'activo') AS estado
            FROM profesor
            {where_sql}
            ORDER BY id
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        resultado = cursor.fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [
                {
                    "id": row[0],
                    "nombre": row[1],
                    "apellido": row[2],
                    "documento": row[3],
                    "email": row[4],
                    "telefono": row[5],
                    "sueldo": row[6],
                    "estado": row[7]
                }
                for row in resultado
            ]
        }
    finally:
        cursor.close()
        conn.close()

def obtener_clases_profesor_controller(profesor_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            a.id,
            c.nombre AS curso,
            m.nombre AS materia
        FROM asignaciones a
        JOIN cursos c ON c.id = a.curso_id
        JOIN materias m ON m.id = a.materia_id
        WHERE a.profesor_id = %s
    """, (profesor_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "asignacion_id": r[0],
            "curso": r[1],
            "materia": r[2]
        }
        for r in rows
    ]
def actualizar_profesor_controller(profesor_id, profesor):
    conn = get_connection()
    cursor = conn.cursor()
    estado = (
        normalizar_estado_profesor(profesor.estado)
        if getattr(profesor, "estado", None) is not None
        else None
    )

    if profesor.password:
        cursor.execute('''
            UPDATE profesor
            SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, telefono = %s, password = %s, sueldo = %s, estado = COALESCE(%s, estado, 'activo')
            WHERE id = %s
        ''', (_title_case_es(profesor.nombre), _title_case_es(profesor.apellido), profesor.documento_identidad, str(profesor.email).strip().lower(), profesor.telefono, get_password_hash(profesor.password), profesor.sueldo, estado, profesor_id))
    else:
        cursor.execute('''
            UPDATE profesor 
            SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, telefono = %s, sueldo = %s, estado = COALESCE(%s, estado, 'activo')
            WHERE id = %s
        ''', (_title_case_es(profesor.nombre), _title_case_es(profesor.apellido), profesor.documento_identidad, str(profesor.email).strip().lower(), profesor.telefono, profesor.sueldo, estado, profesor_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Profesor actualizado correctamente"}


def actualizar_estado_profesor_controller(profesor_id, estado):
    estado_normalizado = normalizar_estado_profesor(estado)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE profesor
            SET estado = %s
            WHERE id = %s
            RETURNING id, COALESCE(LOWER(estado), 'activo')
            """,
            (estado_normalizado, profesor_id),
        )
        row = cursor.fetchone()
        if not row:
            conn.rollback()
            return {"error": "Profesor no encontrado"}
        conn.commit()
        return {
            "mensaje": "Estado de profesor actualizado",
            "id": row[0],
            "estado": row[1],
        }
    finally:
        cursor.close()
        conn.close()
