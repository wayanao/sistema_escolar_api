from app.database import get_connection
from app.security import get_password_hash
from psycopg2 import IntegrityError

ESTADOS_PROFESOR = {"activo", "inactivo"}
ESTADOS_FILTRO_PROFESOR = ESTADOS_PROFESOR | {"todos"}


class ProfesorDuplicadoError(Exception):
    """Se lanza cuando ya existe un profesor con el mismo documento o email."""


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


def _upper_text(value):
    return " ".join(str(value or "").strip().split()).upper()


def _clean_text(value):
    return " ".join(str(value or "").strip().split())


def _normalizar_email(value):
    return str(value or "").strip().lower()


def _validar_campos_profesor(nombre, apellido, documento, email):
    if not nombre:
        raise ValueError("El nombre del profesor es obligatorio.")
    if not apellido:
        raise ValueError("El apellido del profesor es obligatorio.")
    if not documento:
        raise ValueError("El documento del profesor es obligatorio.")
    if not email:
        raise ValueError("El email del profesor es obligatorio.")


def _validar_profesor_unico(cursor, documento, email, profesor_id=None):
    cursor.execute(
        """
        SELECT id
        FROM profesor
        WHERE TRIM(documento_identidad) = %s
          AND (%s IS NULL OR id <> %s)
        LIMIT 1
        """,
        (documento, profesor_id, profesor_id),
    )
    if cursor.fetchone():
        raise ProfesorDuplicadoError(
            f"Ya existe un profesor con el documento '{documento}'."
        )

    cursor.execute(
        """
        SELECT id
        FROM profesor
        WHERE LOWER(TRIM(email)) = %s
          AND (%s IS NULL OR id <> %s)
        LIMIT 1
        """,
        (email, profesor_id, profesor_id),
    )
    if cursor.fetchone():
        raise ProfesorDuplicadoError(
            f"Ya existe un profesor con el email '{email}'."
        )


# 🎯 Crear profesor
def crear_profesor_controller(profesor):

    conn = get_connection()
    cursor = conn.cursor()
    try:
        nombre = _upper_text(profesor.nombre)
        apellido = _upper_text(profesor.apellido)
        documento = _clean_text(profesor.documento_identidad)
        email = _normalizar_email(profesor.email)
        estado = normalizar_estado_profesor(getattr(profesor, "estado", None))

        _validar_campos_profesor(nombre, apellido, documento, email)
        _validar_profesor_unico(cursor, documento, email)

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
            nombre,
            apellido,
            documento,
            email,
            profesor.telefono,
            get_password_hash(profesor.password),
            profesor.sueldo,
            estado
        ))
        profesor_id = cursor.fetchone()[0]

        conn.commit()
        return profesor_id
    except (ProfesorDuplicadoError, ValueError):
        conn.rollback()
        raise
    except IntegrityError as exc:
        conn.rollback()
        raise ProfesorDuplicadoError(
            "Ya existe un profesor con ese documento o email."
        ) from exc
    finally:
        cursor.close()
        conn.close()


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
    try:
        nombre = _upper_text(profesor.nombre)
        apellido = _upper_text(profesor.apellido)
        documento = _clean_text(profesor.documento_identidad)
        email = _normalizar_email(profesor.email)
        estado = (
            normalizar_estado_profesor(profesor.estado)
            if getattr(profesor, "estado", None) is not None
            else None
        )

        _validar_campos_profesor(nombre, apellido, documento, email)
        _validar_profesor_unico(cursor, documento, email, profesor_id)

        if profesor.password:
            cursor.execute('''
                UPDATE profesor
                SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, telefono = %s, password = %s, sueldo = %s, estado = COALESCE(%s, estado, 'activo')
                WHERE id = %s
                RETURNING id
            ''', (nombre, apellido, documento, email, profesor.telefono, get_password_hash(profesor.password), profesor.sueldo, estado, profesor_id))
        else:
            cursor.execute('''
                UPDATE profesor
                SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, telefono = %s, sueldo = %s, estado = COALESCE(%s, estado, 'activo')
                WHERE id = %s
                RETURNING id
            ''', (nombre, apellido, documento, email, profesor.telefono, profesor.sueldo, estado, profesor_id))

        if not cursor.fetchone():
            conn.rollback()
            return {"error": "Profesor no encontrado"}

        conn.commit()
        return {"mensaje": "Profesor actualizado correctamente"}
    except (ProfesorDuplicadoError, ValueError):
        conn.rollback()
        raise
    except IntegrityError as exc:
        conn.rollback()
        raise ProfesorDuplicadoError(
            "Ya existe un profesor con ese documento o email."
        ) from exc
    finally:
        cursor.close()
        conn.close()


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
