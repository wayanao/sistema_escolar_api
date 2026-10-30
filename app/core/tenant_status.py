from datetime import date, timedelta

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


def calculate_effective_tenant_status(
    estado: str | None,
    fecha_proximo_pago=None,
    dias_gracia: int | None = 0,
    today: date | None = None,
) -> str:
    normalized = normalize_tenant_status(estado)
    if normalized in {TENANT_STATUS_SUSPENDED, TENANT_STATUS_CANCELLED}:
        return normalized

    if not fecha_proximo_pago:
        return normalized

    current_date = today or date.today()
    if isinstance(fecha_proximo_pago, str):
        fecha_pago = date.fromisoformat(fecha_proximo_pago)
    else:
        fecha_pago = fecha_proximo_pago

    grace_days = int(dias_gracia or 0)
    if current_date <= fecha_pago:
        return normalized

    if current_date <= fecha_pago + timedelta(days=grace_days):
        return TENANT_STATUS_PAST_DUE

    return TENANT_STATUS_SUSPENDED


def _query_public_colegio(where_sql: str, params: tuple) -> dict | None:
    token = tenant_schema_var.set("public")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            SELECT
                c.id,
                c.nombre,
                c.subdominio,
                c.esquema_db,
                c.estado,
                s.fecha_proximo_pago,
                s.dias_gracia
            FROM colegios c
            LEFT JOIN public.tenant_suscripciones s ON s.tenant_id = c.id
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
            "estado": calculate_effective_tenant_status(row[4], row[5], row[6]),
        }
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)


def get_tenant_by_code(codigo_colegio: str) -> dict | None:
    codigo = str(codigo_colegio or "").strip().lower()
    return _query_public_colegio("c.subdominio = %s", (codigo,))


def get_tenant_by_schema(schema_name: str) -> dict | None:
    return _query_public_colegio("c.esquema_db = %s", (schema_name,))


def colegio_usa_entrevista_admision(schema_name: str) -> bool:
    """Si el colegio usa la entrevista de admisión (2026-10-30).

    Consulta aparte de `_query_public_colegio` a propósito: esa corre en cada
    petición autenticada y en el login, y así una falla de esta columna no
    deja a nadie sin entrar. Ver docs/funcionalidades/ENTREVISTA_ADMISION.md.
    """
    token = tenant_schema_var.set("public")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT usa_entrevista_admision
            FROM colegios
            WHERE esquema_db = %s
            """,
            (schema_name,),
        )
        row = cursor.fetchone()
        return bool(row and row[0])
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)


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
