from app.database import get_connection
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate

def crear_usuario_controller(usuario: UsuarioCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO usuarios (nombre, email, password, rol)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (usuario.nombre, usuario.email, usuario.password, usuario.rol))

    user_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return {"id": user_id, "mensaje": "Usuario creado exitosamente"}

def obtener_usuarios_controller():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre, email, rol FROM usuarios")
    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{"id": u[0], "nombre": u[1], "email": u[2], "rol": u[3]} for u in usuarios]

def actualizar_usuario_controller(user_id: int, usuario: UsuarioUpdate):
    conn = get_connection()
    cursor = conn.cursor()

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
        values.append(usuario.password)

    if not updates:
        return {"error": "No hay campos para actualizar"}

    query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s"
    values.append(user_id)

    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()

    return {"mensaje": "Usuario actualizado exitosamente"}

def eliminar_usuario_controller(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return {"mensaje": "Usuario eliminado exitosamente"}