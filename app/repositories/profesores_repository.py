def obtener_profesor_por_documento(cursor, documento, profesor_id=None):
    cursor.execute(
        """
        SELECT id
        FROM profesor
        WHERE TRIM(documento_identidad) = %s
          AND (%s IS NULL OR id <> %s)
        LIMIT 1
        """,
        (documento, profesor_id, profesor_id),
    )
    return cursor.fetchone()


def obtener_profesor_por_email(cursor, email, profesor_id=None):
    cursor.execute(
        """
        SELECT id
        FROM profesor
        WHERE LOWER(TRIM(email)) = %s
          AND (%s IS NULL OR id <> %s)
        LIMIT 1
        """,
        (email, profesor_id, profesor_id),
    )
    return cursor.fetchone()


def crear_profesor(cursor, parametros):
    cursor.execute("""
            INSERT INTO profesor (
                nombre,
                apellido,
                documento_identidad,
                email,
                telefono,
                password,
                sueldo,
                estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, parametros)
    return cursor.fetchone()[0]


def listar_profesores(cursor, where_sql, params):
    cursor.execute(f"""
            SELECT
                id,
                nombre,
                apellido,
                documento_identidad,
                email,
                telefono,
                sueldo,
                COALESCE(LOWER(estado), 'activo') AS estado
            FROM profesor
            {where_sql}
            ORDER BY id
        """, params)
    return cursor.fetchall()


def contar_profesores(cursor, where_sql, params):
    cursor.execute(f"SELECT COUNT(*) FROM profesor {where_sql}", params)
    return cursor.fetchone()[0]


def listar_profesores_paginados(cursor, where_sql, params):
    cursor.execute(f"""
            SELECT
                id,
                nombre,
                apellido,
                documento_identidad,
                email,
                telefono,
                sueldo,
                COALESCE(LOWER(estado), 'activo') AS estado
            FROM profesor
            {where_sql}
            ORDER BY id
            LIMIT %s OFFSET %s
        """, params)
    return cursor.fetchall()


def actualizar_profesor_con_password(cursor, parametros):
    cursor.execute('''
                UPDATE profesor
                SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, telefono = %s, password = %s, sueldo = %s, estado = COALESCE(%s, estado, 'activo')
                WHERE id = %s
                RETURNING id
            ''', parametros)
    return cursor.fetchone()


def actualizar_profesor_sin_password(cursor, parametros):
    cursor.execute('''
                UPDATE profesor
                SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, telefono = %s, sueldo = %s, estado = COALESCE(%s, estado, 'activo')
                WHERE id = %s
                RETURNING id
            ''', parametros)
    return cursor.fetchone()


def actualizar_estado_profesor(cursor, estado, profesor_id):
    cursor.execute(
        """
            UPDATE profesor
            SET estado = %s
            WHERE id = %s
            RETURNING id, COALESCE(LOWER(estado), 'activo')
            """,
        (estado, profesor_id),
    )
    return cursor.fetchone()
