from app.database import get_connection, get_cursor
from app.repositories import profesores_repository
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
    if profesores_repository.obtener_profesor_por_documento(
        cursor,
        documento,
        profesor_id,
    ):
        raise ProfesorDuplicadoError(
            f"Ya existe un profesor con el documento '{documento}'."
        )

    if profesores_repository.obtener_profesor_por_email(
        cursor,
        email,
        profesor_id,
    ):
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

        profesor_id = profesores_repository.crear_profesor(
            cursor,
            (
                nombre,
                apellido,
                documento,
                email,
                profesor.telefono,
                get_password_hash(profesor.password),
                profesor.sueldo,
                estado,
            ),
        )

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

        resultado = profesores_repository.listar_profesores(
            cursor,
            where_sql,
            params,
        )
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

        total = profesores_repository.contar_profesores(cursor, where_sql, params)
        resultado = profesores_repository.listar_profesores_paginados(
            cursor,
            where_sql,
            params + [limit, offset],
        )

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

    with get_cursor() as cursor:
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
            row = profesores_repository.actualizar_profesor_con_password(
                cursor,
                (
                    nombre,
                    apellido,
                    documento,
                    email,
                    profesor.telefono,
                    get_password_hash(profesor.password),
                    profesor.sueldo,
                    estado,
                    profesor_id,
                ),
            )
        else:
            row = profesores_repository.actualizar_profesor_sin_password(
                cursor,
                (
                    nombre,
                    apellido,
                    documento,
                    email,
                    profesor.telefono,
                    profesor.sueldo,
                    estado,
                    profesor_id,
                ),
            )

        if not row:
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
        row = profesores_repository.actualizar_estado_profesor(
            cursor,
            estado_normalizado,
            profesor_id,
        )
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
