from app.database import get_connection
from app.security import get_password_hash, password_policy_errors, verify_password
from app.globals import tenant_schema_var
from fastapi import HTTPException, status
from app.core.tenant_status import (
    TenantLoginBlocked,
    get_tenant_by_code,
    get_tenant_login_block_message,
    is_tenant_allowed_for_login,
)
from app.core.super_admin import authenticate_super_admin, is_super_admin_login_code

def login_controller(email, password, codigo_colegio):
    if is_super_admin_login_code(codigo_colegio):
        return authenticate_super_admin(email, password, verify_password)

    colegio = get_tenant_by_code(codigo_colegio)

    if not colegio:
        return None

    if not is_tenant_allowed_for_login(colegio["estado"]):
        raise TenantLoginBlocked(
            colegio["estado"],
            get_tenant_login_block_message(colegio["estado"]),
        )

    esquema_db = colegio["esquema_db"]

    # 2. Cambiar la BD al esquema específico del colegio
    tenant_schema_var.set(esquema_db)
    
    # Ahora la nueva conexión apuntará a este colegio
    conn = get_connection()
    cursor = conn.cursor()

    # 3. Buscar en tabla usuarios (Admin/etc en el contexto del Tenant)
    cursor.execute("""
        SELECT id, nombre, email, rol, password, debe_cambiar_password
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
                "tenant": esquema_db,
                "tenant_estado": colegio["estado"],
                "debe_cambiar_password": bool(user[5]),
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
                "tenant": esquema_db,
                "tenant_estado": colegio["estado"],
                "debe_cambiar_password": False,
            }

    return None


def cambiar_password_actual_controller(current_user: dict, password_actual: str, password_nueva: str) -> dict:
    if current_user.get("rol") == "profesor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los profesores no usan este flujo de cambio obligatorio",
        )

    errors = password_policy_errors(password_nueva)
    if errors:
        raise HTTPException(
            status_code=422,
            detail=f"La nueva password debe incluir {', '.join(errors)}",
        )
    if password_actual == password_nueva:
        raise HTTPException(status_code=422, detail="La nueva password debe ser diferente")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT password
            FROM usuarios
            WHERE id = %s
            """,
            (current_user["id"],),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        hashed_pw = row[0]
        if hashed_pw.startswith("$2b$") or hashed_pw.startswith("$2a$"):
            is_valid = verify_password(password_actual, hashed_pw)
        else:
            is_valid = password_actual == hashed_pw

        if not is_valid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password actual incorrecta")

        cursor.execute(
            """
            UPDATE usuarios
            SET password = %s,
                debe_cambiar_password = FALSE
            WHERE id = %s
            """,
            (get_password_hash(password_nueva), current_user["id"]),
        )
        conn.commit()
        return {"mensaje": "Password actualizada", "debe_cambiar_password": False}
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
