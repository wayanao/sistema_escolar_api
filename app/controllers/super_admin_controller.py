import re
from datetime import date
from pathlib import Path

import psycopg2
from fastapi import HTTPException, status
from psycopg2 import sql

from app.config import settings
from app.core.tenant_status import (
    TENANT_STATUSES,
    calculate_effective_tenant_status,
    normalize_tenant_status,
)
from app.database import get_connection
from app.globals import tenant_schema_var
from app.repositories import super_admin_repository
from app.security import get_password_hash, password_policy_errors


TENANT_CODE_PATTERN = re.compile(r"^[a-z0-9_]{3,50}$")

# Esquema base de un tenant, extraido del catalogo real y versionado. Se nombra
# explicitamente en vez de buscar el ultimo archivo del directorio: cambiar de
# esquema base debe ser una edicion visible en el diff, no un efecto colateral
# de anadir un archivo.
ESQUEMA_BASE_TENANT = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "base"
    / "20260813_esquema_base_tenant.sql"
)


def _public_connection():
    token = tenant_schema_var.set("public")
    conn = get_connection()
    return token, conn


def listar_tenants_controller() -> list[dict]:
    token, conn = _public_connection()
    cursor = conn.cursor()
    try:
        return [
            {
                "id": row[0],
                "nombre": row[1],
                "subdominio": row[2],
                "esquema_db": row[3],
                "estado": calculate_effective_tenant_status(row[4], row[6], row[7]),
                "estado_manual": normalize_tenant_status(row[4]),
                "fecha_inicio": row[5].isoformat() if hasattr(row[5], "isoformat") else row[5],
                "fecha_proximo_pago": row[6].isoformat() if hasattr(row[6], "isoformat") else row[6],
                "dias_gracia": row[7],
            }
            for row in super_admin_repository.listar_tenants(cursor)
        ]
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)


def listar_auditoria_tenant_controller(tenant_id: int) -> list[dict]:
    token, conn = _public_connection()
    cursor = conn.cursor()
    try:
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
            for row in super_admin_repository.listar_auditoria_tenant(
                cursor,
                tenant_id,
            )
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
        current = super_admin_repository.obtener_tenant_para_estado(
            cursor,
            tenant_id,
        )
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
                "estado": calculate_effective_tenant_status(current[4], current[6], current[7]),
                "estado_manual": estado_anterior,
                "fecha_inicio": current[5].isoformat() if hasattr(current[5], "isoformat") else current[5],
                "fecha_proximo_pago": current[6].isoformat() if hasattr(current[6], "isoformat") else current[6],
                "dias_gracia": current[7],
            }

        row = super_admin_repository.actualizar_estado_tenant(
            cursor,
            estado_normalizado,
            tenant_id,
        )
        super_admin_repository.registrar_auditoria_estado(
            cursor,
            tenant_id,
            estado_anterior,
            estado_normalizado,
            motivo_limpio,
            super_admin_id,
        )

        conn.commit()
        return {
            "id": row[0],
            "nombre": row[1],
            "subdominio": row[2],
            "esquema_db": row[3],
            "estado": calculate_effective_tenant_status(row[4], current[6], current[7]),
            "estado_manual": normalize_tenant_status(row[4]),
            "fecha_inicio": current[5].isoformat() if hasattr(current[5], "isoformat") else current[5],
            "fecha_proximo_pago": current[6].isoformat() if hasattr(current[6], "isoformat") else current[6],
            "dias_gracia": current[7],
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


def _validar_password_fuerte(password: str) -> None:
    errors = password_policy_errors(password)
    if errors:
        raise HTTPException(
            status_code=422,
            detail=f"La password temporal debe incluir {', '.join(errors)}",
        )


def crear_tenant_controller(data: dict, super_admin_id: int | None = None) -> dict:
    nombre = str(data.get("nombre") or "").strip()
    codigo = str(data.get("codigo") or "").strip().lower().replace(" ", "_")
    admin_nombre = str(data.get("admin_nombre") or "").strip()
    admin_email = str(data.get("admin_email") or "").strip().lower()
    admin_password = str(data.get("admin_password") or "")
    fecha_inicio = data.get("fecha_inicio")
    fecha_proximo_pago = data.get("fecha_proximo_pago")
    dias_gracia = int(data.get("dias_gracia") or 0)
    notas = str(data.get("notas") or "").strip() or None

    if not nombre:
        raise HTTPException(status_code=422, detail="Nombre de colegio requerido")
    if not TENANT_CODE_PATTERN.fullmatch(codigo):
        raise HTTPException(status_code=422, detail="Codigo de colegio invalido")
    if not admin_nombre or not admin_email or not admin_password:
        raise HTTPException(status_code=422, detail="Datos del admin inicial incompletos")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", admin_email):
        raise HTTPException(status_code=422, detail="Correo del admin invalido")
    _validar_password_fuerte(admin_password)
    if dias_gracia < 0:
        raise HTTPException(status_code=422, detail="Dias de gracia invalido")

    try:
        fecha_inicio_date = date.fromisoformat(str(fecha_inicio))
        fecha_proximo_pago_date = date.fromisoformat(str(fecha_proximo_pago))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Fechas de suscripcion invalidas") from exc

    if fecha_proximo_pago_date < fecha_inicio_date:
        raise HTTPException(status_code=422, detail="La proxima fecha de pago no puede ser anterior al inicio")

    esquema_nuevo = f"tenant_{codigo}"
    template_schema = settings.DEFAULT_TENANT_SCHEMA

    token, conn = _public_connection()
    cursor = conn.cursor()
    try:
        colegio = super_admin_repository.crear_colegio(
            cursor,
            nombre,
            codigo,
            esquema_nuevo,
        )
        tenant_id = colegio[0]

        super_admin_repository.crear_schema(
            cursor,
            sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(esquema_nuevo)),
        )

        # El schema se construye desde una migracion base versionada, no copiando
        # la plantilla. La copia con LIKE INCLUDING ALL no reproducia las claves
        # foraneas ni creaba secuencias propias, asi que cada tenant nacia sin
        # integridad referencial y compartiendo los contadores de la plantilla.
        #
        # El archivo usa nombres sin cualificar, de modo que el search_path debe
        # apuntar SOLO al schema nuevo mientras se aplica: si la plantilla
        # estuviera en el camino, sus tablas resolverian las referencias y las
        # claves foraneas naceran apuntando a otro schema.
        super_admin_repository.fijar_search_path_base(
            cursor,
            sql.SQL("SET LOCAL search_path TO {}").format(
                sql.Identifier(esquema_nuevo)
            ),
        )
        super_admin_repository.aplicar_esquema_base(
            cursor,
            ESQUEMA_BASE_TENANT.read_text(encoding="utf-8"),
        )

        # El schema nuevo es una copia estructural de la plantilla, asi que
        # hereda exactamente las migraciones que la plantilla tiene aplicadas.
        # Se copian sus filas en vez de leer el directorio migrations/, porque
        # eso supondria que la plantilla esta al dia y nadie lo ha verificado.
        # Sin esto el tenant nace con historial vacio y el runner intentaria
        # aplicarle todas las migraciones sobre tablas que ya las tienen.
        historial = super_admin_repository.obtener_historial_migraciones(cursor)
        if historial and historial[0]:
            super_admin_repository.copiar_historial_migraciones(
                cursor,
                esquema_nuevo,
                template_schema,
            )

        super_admin_repository.fijar_search_path_tenant(
            cursor,
            sql.SQL("SET search_path TO {}, public").format(
                sql.Identifier(esquema_nuevo)
            ),
        )
        super_admin_repository.crear_branding_inicial(cursor)
        super_admin_repository.copiar_plantillas_predefinidas(
            cursor,
            sql.SQL(
                """
                INSERT INTO plantilla_impresion
                    (tipo, nombre, codigo, es_predefinida, activa, config_json)
                SELECT tipo, nombre, codigo, es_predefinida, activa, config_json
                FROM {}.plantilla_impresion
                WHERE es_predefinida = TRUE
                """
            ).format(sql.Identifier(template_schema))
        )
        super_admin_repository.crear_admin_inicial(
            cursor,
            admin_nombre,
            admin_email,
            get_password_hash(admin_password),
        )

        super_admin_repository.restaurar_search_path_public(cursor)
        super_admin_repository.crear_suscripcion(
            cursor,
            tenant_id,
            fecha_inicio_date,
            fecha_proximo_pago_date,
            dias_gracia,
            notas,
        )
        if super_admin_id is not None:
            super_admin_repository.registrar_evento_tenant_creado(
                cursor,
                tenant_id,
                "tenant_creado",
                f"Colegio creado con admin inicial {admin_email}",
                super_admin_id,
            )

        conn.commit()
        return {
            "id": colegio[0],
            "nombre": colegio[1],
            "subdominio": colegio[2],
            "esquema_db": colegio[3],
            "estado": normalize_tenant_status(colegio[4]),
            "estado_manual": normalize_tenant_status(colegio[4]),
            "fecha_inicio": fecha_inicio_date.isoformat(),
            "fecha_proximo_pago": fecha_proximo_pago_date.isoformat(),
            "dias_gracia": dias_gracia,
        }
    except psycopg2.IntegrityError as exc:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El codigo del colegio o el correo del admin ya existe",
        ) from exc
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        tenant_schema_var.reset(token)
