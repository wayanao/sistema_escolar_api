from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import settings
from app.core.tenant_status import ensure_tenant_allowed_for_app
from app.database import get_connection
from app.db.tenant import TENANT_SCHEMA_PATTERN
from app.globals import tenant_schema_var

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


def _columnas_tabla(cursor, tabla: str) -> set[str]:
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = %s
        """,
        (tabla,),
    )
    return {row[0] for row in cursor.fetchall()}


def _valor_activo(valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in {"activo", "activa", "active", "true", "1", "si", "sí"}


def _validar_usuario_en_bd(user_id: int, rol: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if rol == "profesor":
            columnas = _columnas_tabla(cursor, "profesor")
            campos = ["id"]
            if "estado" in columnas:
                campos.append("estado")
            if "activo" in columnas:
                campos.append("activo")

            cursor.execute(
                f"SELECT {', '.join(campos)} FROM profesor WHERE id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Profesor no existe")

            valores_extra = row[1:]
            if not all(_valor_activo(valor) for valor in valores_extra):
                raise ValueError("Profesor inactivo")
            return

        columnas = _columnas_tabla(cursor, "usuarios")
        campos = ["id", "rol"]
        if "estado" in columnas:
            campos.append("estado")
        if "activo" in columnas:
            campos.append("activo")

        cursor.execute(
            f"SELECT {', '.join(campos)} FROM usuarios WHERE id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Usuario no existe")
        if str(row[1]) != rol:
            raise ValueError("Rol desactualizado")

        valores_extra = row[2:]
        if not all(_valor_activo(valor) for valor in valores_extra):
            raise ValueError("Usuario inactivo")
    finally:
        cursor.close()
        conn.close()


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        token = request.cookies.get("token")

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Asegurarnos de soportar variables str o int desde JWT
        user_id = str(payload.get("sub")) if payload.get("sub") else None
        rol = str(payload.get("rol")) if payload.get("rol") else None
        tenant = str(payload.get("tenant")) if payload.get("tenant") else None
        
        if not user_id or not rol or not tenant or not TENANT_SCHEMA_PATTERN.fullmatch(tenant):
            raise credentials_exception
            
        user_id_int = int(user_id)

        ensure_tenant_allowed_for_app(tenant)

        # Configuramos el contexto de esta petición para que la BD apunte al colegio correcto
        tenant_schema_var.set(tenant)
        _validar_usuario_en_bd(user_id_int, rol)
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    return {"id": user_id_int, "rol": rol, "tenant": tenant}

async def get_current_active_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes los permisos necesarios"
        )
    return current_user
