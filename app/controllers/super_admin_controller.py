import re
from datetime import date

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
from app.security import get_password_hash, password_policy_errors


TENANT_CODE_PATTERN = re.compile(r"^[a-z0-9_]{3,50}$")


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
            SELECT
                c.id,
                c.nombre,
                c.subdominio,
                c.esquema_db,
                c.estado,
                s.fecha_inicio,
                s.fecha_proximo_pago,
                s.dias_gracia
            FROM public.colegios c
            LEFT JOIN public.tenant_suscripciones s ON s.tenant_id = c.id
            ORDER BY c.id
            """
        )
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
        cursor.execute(
            """
            SELECT
                c.id,
                c.nombre,
                c.subdominio,
                c.esquema_db,
                c.estado,
                s.fecha_inicio,
                s.fecha_proximo_pago,
                s.dias_gracia
            FROM public.colegios c
            LEFT JOIN public.tenant_suscripciones s ON s.tenant_id = c.id
            WHERE c.id = %s
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
                "estado": calculate_effective_tenant_status(current[4], current[6], current[7]),
                "estado_manual": estado_anterior,
                "fecha_inicio": current[5].isoformat() if hasattr(current[5], "isoformat") else current[5],
                "fecha_proximo_pago": current[6].isoformat() if hasattr(current[6], "isoformat") else current[6],
                "dias_gracia": current[7],
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
        cursor.execute(
            """
            INSERT INTO public.colegios (nombre, subdominio, esquema_db, estado)
            VALUES (%s, %s, %s, 'activo')
            RETURNING id, nombre, subdominio, esquema_db, estado
            """,
            (nombre, codigo, esquema_nuevo),
        )
        colegio = cursor.fetchone()
        tenant_id = colegio[0]

        cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(esquema_nuevo)))
        cursor.execute(
            sql.SQL(
                """
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT tablename
                        FROM pg_tables
                        WHERE schemaname = {template_schema_literal}
                    ) LOOP
                        EXECUTE format(
                            'CREATE TABLE %I.%I (LIKE %I.%I INCLUDING ALL)',
                            {target_schema_literal},
                            r.tablename,
                            {template_schema_literal},
                            r.tablename
                        );
                    END LOOP;
                END $$;
                """
            ).format(
                target_schema_literal=sql.Literal(esquema_nuevo),
                template_schema_literal=sql.Literal(template_schema),
            )
        )

        # El schema nuevo es una copia estructural de la plantilla, asi que
        # hereda exactamente las migraciones que la plantilla tiene aplicadas.
        # Se copian sus filas en vez de leer el directorio migrations/, porque
        # eso supondria que la plantilla esta al dia y nadie lo ha verificado.
        # Sin esto el tenant nace con historial vacio y el runner intentaria
        # aplicarle todas las migraciones sobre tablas que ya las tienen.
        cursor.execute("SELECT to_regclass('public.schema_migrations')")
        historial = cursor.fetchone()
        if historial and historial[0]:
            cursor.execute(
                """
                INSERT INTO public.schema_migrations (migration_name, target_schema, checksum)
                SELECT migration_name, %s, checksum
                FROM public.schema_migrations
                WHERE target_schema = %s
                """,
                (esquema_nuevo, template_schema),
            )

        cursor.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(esquema_nuevo)))
        cursor.execute("INSERT INTO institucion_branding (nombre_institucion) VALUES ('')")
        cursor.execute(
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
        cursor.execute(
            """
            INSERT INTO usuarios (nombre, email, rol, password, debe_cambiar_password)
            VALUES (%s, %s, 'admin', %s, TRUE)
            """,
            (admin_nombre, admin_email, get_password_hash(admin_password)),
        )

        cursor.execute("SET search_path TO public")
        cursor.execute(
            """
            INSERT INTO public.tenant_suscripciones (
                tenant_id,
                fecha_inicio,
                fecha_proximo_pago,
                dias_gracia,
                notas
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (tenant_id, fecha_inicio_date, fecha_proximo_pago_date, dias_gracia, notas),
        )
        if super_admin_id is not None:
            cursor.execute(
                """
                INSERT INTO public.tenant_eventos_auditoria (
                    tenant_id,
                    evento,
                    detalle,
                    super_admin_id
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    tenant_id,
                    "tenant_creado",
                    f"Colegio creado con admin inicial {admin_email}",
                    super_admin_id,
                ),
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
