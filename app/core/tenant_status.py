from fastapi import HTTPException, status

from app.database import get_connection
from app.globals import tenant_schema_var

TENANT_STATUS_ACTIVE = "activo"
TENANT_STATUS_PAST_DUE = "en_mora"
TENANT_STATUS_SUSPENDED = "suspendido"
TENANT_STATUS_CANCELLED = "cancelado"

TENANT_STATUSES = {
    TENANT_STATUS_ACTIVE,
    TENANT_STATUS_PAST_DUE,
    TENANT_STATUS_SUSPENDED,
    TENANT_STATUS_CANCELLED,
}

LOGIN_ALLOWED_STATUSES = {
    TENANT_STATUS_ACTIVE,
    TENANT_STATUS_PAST_DUE,
}

APP_ALLOWED_STATUSES = {
    TENANT_STATUS_ACTIVE,
    TENANT_STATUS_PAST_DUE,
}


class TenantLoginBlocked(Exception):
    def __init__(self, estado: str, message: str):
        self.estado = estado
        self.message = message
        super().__init__(message)


def normalize_tenant_status(value: str | None) -> str:
    if value is None:
        return TENANT_STATUS_SUSPENDED

    normalized = str(value).strip().lower()
    if not normalized:
        return TENANT_STATUS_SUSPENDED

    if normalized in TENANT_STATUSES:
        return normalized
    return TENANT_STATUS_SUSPENDED


def _query_public_colegio(where_sql: str, params: tuple) -> dict | None:
    token = tenant_schema_var.set("public")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            SELECT id, nombre, subdominio, esquema_db, estado
            FROM colegios
            WHERE {where_sql}
            """,
            params,
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "nombre": row[1],
            "subdominio": row[2],
            "esquema_db": row[3],
            "estado": normalize_tenant_status(row[4]),
        }
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)


def get_tenant_by_code(codigo_colegio: str) -> dict | None:
    codigo = str(codigo_colegio or "").strip().lower()
    return _query_public_colegio("subdominio = %s", (codigo,))


def get_tenant_by_schema(schema_name: str) -> dict | None:
    return _query_public_colegio("esquema_db = %s", (schema_name,))


def is_tenant_allowed_for_login(estado: str | None) -> bool:
    return normalize_tenant_status(estado) in LOGIN_ALLOWED_STATUSES


def is_tenant_allowed_for_app(estado: str | None) -> bool:
    return normalize_tenant_status(estado) in APP_ALLOWED_STATUSES


def get_tenant_login_block_message(estado: str | None) -> str:
    normalized = normalize_tenant_status(estado)
    if normalized == TENANT_STATUS_SUSPENDED:
        return "El servicio del colegio se encuentra suspendido. Contacta al administrador de la plataforma."
    if normalized == TENANT_STATUS_CANCELLED:
        return "El servicio del colegio se encuentra cancelado. Contacta al administrador de la plataforma."
    return "El colegio no esta habilitado para iniciar sesion."


def ensure_tenant_allowed_for_app(schema_name: str) -> dict:
    tenant = get_tenant_by_schema(schema_name)
    if not tenant or not is_tenant_allowed_for_app(tenant["estado"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant no autorizado",
        )
    return tenant


def build_tenant_status_response(tenant: dict) -> dict:
    estado = normalize_tenant_status(tenant.get("estado"))
    mostrar_aviso = estado == TENANT_STATUS_PAST_DUE
    mensaje = ""
    if estado == TENANT_STATUS_PAST_DUE:
        mensaje = "Tu servicio se encuentra en mora. Por favor realiza el pago para evitar suspensión."
    elif estado == TENANT_STATUS_SUSPENDED:
        mensaje = "El servicio se encuentra suspendido. Contacta al administrador de la plataforma."
    elif estado == TENANT_STATUS_CANCELLED:
        mensaje = "El servicio se encuentra cancelado. Contacta al administrador de la plataforma."

    return {
        "estado": estado,
        "mostrar_aviso": mostrar_aviso,
        "mensaje": mensaje,
    }
