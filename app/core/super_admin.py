from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.database import get_connection
from app.globals import tenant_schema_var
from app.repositories import super_admin_repository

SUPER_ADMIN_ROLE = "super_admin"
SUPER_ADMIN_TENANT = "public"
SUPER_ADMIN_LOGIN_CODES = {"super_admin", "superadmin", "plataforma"}
super_admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


def is_super_admin_login_code(codigo_colegio: str) -> bool:
    codigo = str(codigo_colegio or "").strip().lower()
    return codigo in SUPER_ADMIN_LOGIN_CODES


def _with_public_connection():
    token = tenant_schema_var.set(SUPER_ADMIN_TENANT)
    conn = get_connection()
    return token, conn


def authenticate_super_admin(email: str, password: str, verify_password) -> dict | None:
    token, conn = _with_public_connection()
    cursor = conn.cursor()
    try:
        row = super_admin_repository.obtener_super_admin_por_email(
            cursor,
            str(email).strip().lower(),
        )
        if not row:
            return None

        estado = str(row[4] or "").strip().lower()
        if estado != "activo":
            return None

        if not verify_password(password, row[3]):
            return None

        return {
            "id": row[0],
            "nombre": row[1],
            "rol": SUPER_ADMIN_ROLE,
            "tenant": SUPER_ADMIN_TENANT,
        }
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)


def validate_super_admin(user_id: int) -> None:
    token, conn = _with_public_connection()
    cursor = conn.cursor()
    try:
        row = super_admin_repository.obtener_estado_super_admin(cursor, user_id)
        if not row or str(row[0] or "").strip().lower() != "activo":
            raise ValueError("Super admin no valido")
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)


async def get_current_super_admin(
    request: Request,
    token: str | None = Depends(super_admin_oauth2_scheme),
):
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
        user_id = str(payload.get("sub")) if payload.get("sub") else None
        rol = str(payload.get("rol")) if payload.get("rol") else None
        tenant = str(payload.get("tenant")) if payload.get("tenant") else None

        if rol != SUPER_ADMIN_ROLE or tenant != SUPER_ADMIN_TENANT or not user_id:
            raise credentials_exception

        user_id_int = int(user_id)
        await run_in_threadpool(validate_super_admin, user_id_int)
    except (JWTError, ValueError):
        raise credentials_exception

    return {"id": user_id_int, "rol": SUPER_ADMIN_ROLE, "tenant": SUPER_ADMIN_TENANT}
