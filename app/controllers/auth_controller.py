from app.database import get_connection
from app.security import verify_password, get_password_hash
from app.globals import tenant_schema_var

def login_controller(email, password, codigo_colegio):
    # Forzamos conextarse a public un momento para validar el colegio
    tenant_schema_var.set("public")
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Buscar si el colegio (subdominio) existe
    cursor.execute("SELECT esquema_db, estado FROM colegios WHERE subdominio = %s", (codigo_colegio,))
    colegio = cursor.fetchone()
    
    if not colegio or colegio[1] != 'activo':
        cursor.close()
        conn.close()
        return None # Colegio no existe o está inactivo
        
    esquema_db = colegio[0]
    cursor.close()
    conn.close()

    # 2. Cambiar la BD al esquema específico del colegio
    tenant_schema_var.set(esquema_db)
    
    # Ahora la nueva conexión apuntará a este colegio
    conn = get_connection()
    cursor = conn.cursor()

    # 3. Buscar en tabla usuarios (Admin/etc en el contexto del Tenant)
    cursor.execute("""
        SELECT id, nombre, email, rol, password
        FROM usuarios
        WHERE email = %s
    """, (email,))

    user = cursor.fetchone()

    if user:
        hashed_pw = user[4]
        is_valid = False

        if hashed_pw.startswith('$2b$') or hashed_pw.startswith('$2a$'):
            is_valid = verify_password(password, hashed_pw)
        else:
            # Contraseña legacy en plano: validar y rehashear inmediatamente
            is_valid = (password == hashed_pw)
            if is_valid:
                cursor.execute(
                    "UPDATE usuarios SET password = %s WHERE id = %s",
                    (get_password_hash(password), user[0])
                )
                conn.commit()

        if is_valid:
            cursor.close()
            conn.close()
            return {
                "id": user[0],
                "nombre": user[1],
                "rol": user[3],
                "tenant": esquema_db
            }

    # Si no está en usuarios o pass inválido, buscar en profesor
    cursor.execute("""
        SELECT id, nombre, apellido, email, password
        FROM profesor
        WHERE email = %s
    """, (email,))

    profesor = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if profesor:
        hashed_pw = profesor[4]
        is_valid = False

        if hashed_pw.startswith('$2b$') or hashed_pw.startswith('$2a$'):
            is_valid = verify_password(password, hashed_pw)
        else:
            # Contraseña legacy en plano: validar y rehashear inmediatamente
            is_valid = (password == hashed_pw)
            if is_valid:
                conn2 = get_connection()
                cur2 = conn2.cursor()
                cur2.execute(
                    "UPDATE profesor SET password = %s WHERE id = %s",
                    (get_password_hash(password), profesor[0])
                )
                conn2.commit()
                cur2.close()
                conn2.close()

        if is_valid:
            return {
                "id": profesor[0],
                "nombre": f"{profesor[1]} {profesor[2]}",
                "rol": "profesor",
                "tenant": esquema_db
            }

    return None