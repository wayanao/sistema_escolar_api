from fastapi import HTTPException, status

from app.core.tenant_status import TENANT_STATUSES, normalize_tenant_status
from app.database import get_connection
from app.globals import tenant_schema_var


TENANT_STATUS_AUDIT_SQL = """
CREATE TABLE IF NOT EXISTS public.tenant_estado_auditoria (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES public.colegios(id),
    estado_anterior VARCHAR(30) NOT NULL,
    estado_nuevo VARCHAR(30) NOT NULL,
    motivo TEXT,
    super_admin_id INTEGER NOT NULL REFERENCES public.super_admins(id),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_estado_auditoria_tenant_id
ON public.tenant_estado_auditoria (tenant_id);

CREATE INDEX IF NOT EXISTS idx_tenant_estado_auditoria_creado_en
ON public.tenant_estado_auditoria (creado_en);
"""


def _public_connection():
    token = tenant_schema_var.set("public")
    conn = get_connection()
    return token, conn


def listar_tenants_controller() -> list[dict]:
    token, conn = _public_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, nombre, subdominio, esquema_db, estado
            FROM public.colegios
            ORDER BY id
            """
        )
        return [
            {
                "id": row[0],
                "nombre": row[1],
                "subdominio": row[2],
                "esquema_db": row[3],
                "estado": normalize_tenant_status(row[4]),
            }
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)


def listar_auditoria_tenant_controller(tenant_id: int) -> list[dict]:
    token, conn = _public_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(TENANT_STATUS_AUDIT_SQL)
        cursor.execute(
            """
            SELECT
                a.id,
                a.estado_anterior,
                a.estado_nuevo,
                a.motivo,
                a.creado_en,
                s.nombre,
                s.email
            FROM public.tenant_estado_auditoria a
            JOIN public.super_admins s ON s.id = a.super_admin_id
            WHERE a.tenant_id = %s
            ORDER BY a.creado_en DESC
            LIMIT 50
            """,
            (tenant_id,),
        )
        return [
            {
                "id": row[0],
                "estado_anterior": normalize_tenant_status(row[1]),
                "estado_nuevo": normalize_tenant_status(row[2]),
                "motivo": row[3],
                "creado_en": row[4].isoformat() if hasattr(row[4], "isoformat") else row[4],
                "super_admin_nombre": row[5],
                "super_admin_email": row[6],
            }
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)


def actualizar_estado_tenant_controller(
    tenant_id: int,
    estado: str,
    super_admin_id: int,
    motivo: str | None = None,
) -> dict:
    estado_normalizado = str(estado or "").strip().lower()
    if estado_normalizado not in TENANT_STATUSES:
        raise HTTPException(status_code=422, detail="Estado de tenant invalido")

    motivo_limpio = str(motivo or "").strip() or None

    token, conn = _public_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(TENANT_STATUS_AUDIT_SQL)
        cursor.execute(
            """
            SELECT id, nombre, subdominio, esquema_db, estado
            FROM public.colegios
            WHERE id = %s
            """,
            (tenant_id,),
        )
        current = cursor.fetchone()
        if not current:
            conn.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

        estado_anterior = normalize_tenant_status(current[4])
        if estado_anterior == estado_normalizado:
            conn.rollback()
            return {
                "id": current[0],
                "nombre": current[1],
                "subdominio": current[2],
                "esquema_db": current[3],
                "estado": estado_anterior,
            }

        cursor.execute(
            """
            UPDATE public.colegios
            SET estado = %s
            WHERE id = %s
            RETURNING id, nombre, subdominio, esquema_db, estado
            """,
            (estado_normalizado, tenant_id),
        )
        row = cursor.fetchone()
        cursor.execute(
            """
            INSERT INTO public.tenant_estado_auditoria (
                tenant_id,
                estado_anterior,
                estado_nuevo,
                motivo,
                super_admin_id
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (tenant_id, estado_anterior, estado_normalizado, motivo_limpio, super_admin_id),
        )

        conn.commit()
        return {
            "id": row[0],
            "nombre": row[1],
            "subdominio": row[2],
            "esquema_db": row[3],
            "estado": normalize_tenant_status(row[4]),
        }
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)
