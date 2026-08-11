from app.database import get_connection, get_cursor
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.security import get_password_hash

def crear_usuario_controller(usuario: UsuarioCreate):
    with get_cursor(commit=True) as cursor:
        hashed_password = get_password_hash(usuario.password)

        cursor.execute("""
            INSERT INTO usuarios (nombre, email, password, rol)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (usuario.nombre, usuario.email, hashed_password, usuario.rol))

        user_id = cursor.fetchone()[0]

    return {"id": user_id, "mensaje": "Usuario creado exitosamente"}

def obtener_usuarios_controller():
    with get_cursor() as cursor:
        cursor.execute("SELECT id, nombre, email, rol FROM usuarios")
        usuarios = cursor.fetchall()

    return [{"id": u[0], "nombre": u[1], "email": u[2], "rol": u[3]} for u in usuarios]

def obtener_usuarios_paginado_controller(limit=50, offset=0, busqueda=None, rol=None):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        filtros = []
        params = []

        if rol:
            filtros.append("rol = %s")
            params.append(rol)

        if busqueda:
            filtros.append("(LOWER(nombre) LIKE LOWER(%s) OR LOWER(email) LIKE LOWER(%s))")
            patron = f"%{busqueda}%"
            params.extend([patron, patron])

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"SELECT COUNT(*) FROM usuarios {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, nombre, email, rol
            FROM usuarios
            {where_sql}
            ORDER BY id
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        usuarios = cursor.fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [{"id": u[0], "nombre": u[1], "email": u[2], "rol": u[3]} for u in usuarios]
        }
    finally:
        cursor.close()
        conn.close()

def actualizar_usuario_controller(user_id: int, usuario: UsuarioUpdate):
    updates = []
    values = []

    if usuario.nombre is not None:
        updates.append("nombre = %s")
        values.append(usuario.nombre)
    if usuario.email is not None:
        updates.append("email = %s")
        values.append(usuario.email)
    if usuario.rol is not None:
        updates.append("rol = %s")
        values.append(usuario.rol)
    if usuario.password is not None:
        updates.append("password = %s")
        values.append(get_password_hash(usuario.password))

    if not updates:
        return {"error": "No hay campos para actualizar"}

    query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s"
    values.append(user_id)

    with get_cursor(commit=True) as cursor:
        cursor.execute(query, values)

    return {"mensaje": "Usuario actualizado exitosamente"}

def eliminar_usuario_controller(user_id: int):
    with get_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))

    return {"mensaje": "Usuario eliminado exitosamente"}
