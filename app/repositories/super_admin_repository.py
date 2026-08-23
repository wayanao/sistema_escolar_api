def listar_tenants(cursor):
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
    return cursor.fetchall()


def listar_auditoria_tenant(cursor, tenant_id):
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
    return cursor.fetchall()


def obtener_tenant_para_estado(cursor, tenant_id):
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
    return cursor.fetchone()


def actualizar_estado_tenant(cursor, estado, tenant_id):
    cursor.execute(
        """
            UPDATE public.colegios
            SET estado = %s
            WHERE id = %s
            RETURNING id, nombre, subdominio, esquema_db, estado
            """,
        (estado, tenant_id),
    )
    return cursor.fetchone()


def registrar_auditoria_estado(
    cursor,
    tenant_id,
    estado_anterior,
    estado_nuevo,
    motivo,
    super_admin_id,
):
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
        (tenant_id, estado_anterior, estado_nuevo, motivo, super_admin_id),
    )
