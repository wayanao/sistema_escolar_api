def obtener_branding(cursor):
    cursor.execute("""
            SELECT id, nombre_institucion, eslogan, logo_principal_url, logo_secundario_url,
                   direccion, telefono, email, nit, codigo_dane, sitio_web,
                   color_primario, color_secundario, configuracion_extra
            FROM institucion_branding
            ORDER BY id ASC
            LIMIT 1
        """)
    return cursor.fetchone()


def crear_branding(cursor):
    cursor.execute("""
                INSERT INTO institucion_branding (nombre_institucion)
                VALUES ('')
                RETURNING id, nombre_institucion, eslogan, logo_principal_url, logo_secundario_url,
                         direccion, telefono, email, nit, codigo_dane, sitio_web,
                         color_primario, color_secundario, configuracion_extra
            """)
    return cursor.fetchone()


def actualizar_branding(cursor, parametros):
    cursor.execute("""
            UPDATE institucion_branding
            SET nombre_institucion = %s,
                eslogan = %s,
                direccion = %s,
                telefono = %s,
                email = %s,
                nit = %s,
                codigo_dane = %s,
                sitio_web = %s,
                color_primario = %s,
                color_secundario = %s,
                configuracion_extra = %s,
                actualizado_en = CURRENT_TIMESTAMP
            WHERE id = (SELECT id FROM institucion_branding ORDER BY id ASC LIMIT 1)
        """, parametros)


def obtener_logo(cursor, columna):
    cursor.execute(f"""
            SELECT {columna} FROM institucion_branding
            ORDER BY id ASC LIMIT 1
        """)
    return cursor.fetchone()


def actualizar_logo(cursor, columna, nueva_url):
    cursor.execute(f"""
            UPDATE institucion_branding
            SET {columna} = %s,
                actualizado_en = CURRENT_TIMESTAMP
            WHERE id = (SELECT id FROM institucion_branding ORDER BY id ASC LIMIT 1)
        """, (nueva_url,))


def eliminar_logo(cursor, columna):
    cursor.execute(f"""
            UPDATE institucion_branding
            SET {columna} = NULL,
                actualizado_en = CURRENT_TIMESTAMP
            WHERE id = (SELECT id FROM institucion_branding ORDER BY id ASC LIMIT 1)
        """)
