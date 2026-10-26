def obtener_super_admin_por_email(cursor, email):
    cursor.execute(
        """
            SELECT id, nombre, email, password, estado
            FROM public.super_admins
            WHERE email = %s
            """,
        (email,),
    )
    return cursor.fetchone()


def obtener_estado_super_admin(cursor, super_admin_id):
    cursor.execute(
        """
            SELECT estado
            FROM public.super_admins
            WHERE id = %s
            """,
        (super_admin_id,),
    )
    return cursor.fetchone()


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


def actualizar_proximo_pago(cursor, tenant_id, fecha_proximo_pago):
    cursor.execute(
        """
            UPDATE public.tenant_suscripciones
            SET fecha_proximo_pago = %s,
                actualizado_en = NOW()
            WHERE tenant_id = %s
            """,
        (fecha_proximo_pago, tenant_id),
    )


def crear_colegio(cursor, nombre, codigo, esquema_nuevo):
    cursor.execute(
        """
            INSERT INTO public.colegios (nombre, subdominio, esquema_db, estado)
            VALUES (%s, %s, %s, 'activo')
            RETURNING id, nombre, subdominio, esquema_db, estado
            """,
        (nombre, codigo, esquema_nuevo),
    )
    return cursor.fetchone()


def crear_schema(cursor, query):
    cursor.execute(query)


def fijar_search_path_base(cursor, query):
    cursor.execute(query)


def aplicar_esquema_base(cursor, esquema_base):
    cursor.execute(esquema_base)


def obtener_historial_migraciones(cursor):
    cursor.execute("SELECT to_regclass('public.schema_migrations')")
    return cursor.fetchone()


def copiar_historial_migraciones(cursor, esquema_nuevo, template_schema):
    cursor.execute(
        """
                INSERT INTO public.schema_migrations (migration_name, target_schema, checksum)
                SELECT migration_name, %s, checksum
                FROM public.schema_migrations
                WHERE target_schema = %s
                """,
        (esquema_nuevo, template_schema),
    )


def fijar_search_path_tenant(cursor, query):
    cursor.execute(query)


def crear_branding_inicial(cursor):
    cursor.execute("INSERT INTO institucion_branding (nombre_institucion) VALUES ('')")


def copiar_plantillas_predefinidas(cursor, query):
    cursor.execute(query)


def crear_admin_inicial(cursor, admin_nombre, admin_email, password_hash):
    cursor.execute(
        """
            INSERT INTO usuarios (nombre, email, rol, password, debe_cambiar_password)
            VALUES (%s, %s, 'admin', %s, TRUE)
            """,
        (admin_nombre, admin_email, password_hash),
    )


def restaurar_search_path_public(cursor):
    cursor.execute("SET search_path TO public")


def crear_suscripcion(
    cursor,
    tenant_id,
    fecha_inicio,
    fecha_proximo_pago,
    dias_gracia,
    notas,
):
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
        (tenant_id, fecha_inicio, fecha_proximo_pago, dias_gracia, notas),
    )


def registrar_evento_tenant_creado(
    cursor,
    tenant_id,
    evento,
    detalle,
    super_admin_id,
):
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
        (tenant_id, evento, detalle, super_admin_id),
    )
