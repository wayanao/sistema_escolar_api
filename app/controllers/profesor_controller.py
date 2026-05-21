from app.database import get_connection
from app.security import get_password_hash


# 🎯 Crear profesor
def crear_profesor_controller(profesor):

    # 🔌 Abrimos conexión
    conn = get_connection()
    cursor = conn.cursor()

    # 🧠 Insertamos en la base de datos (AGREGAMOS EMAIL)
    cursor.execute("""
        INSERT INTO profesor (
            nombre,
            apellido,
            documento_identidad,
            email,
            telefono,
            password,
            sueldo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        profesor.nombre,
        profesor.apellido,
        profesor.documento_identidad,
        profesor.email,
        profesor.telefono,
        get_password_hash(profesor.password),
        profesor.sueldo
    ))
    # 📥 Obtener ID
    profesor_id = cursor.fetchone()[0]

    # 💾 Guardar cambios
    conn.commit()

    # 🔒 Cerrar conexión
    cursor.close()
    conn.close()

    return profesor_id


# 🎯 Obtener todos los profesores
def obtener_profesores_controller():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            nombre,
            apellido,
            documento_identidad,
            email,
            telefono,
            sueldo
        FROM profesor
        ORDER BY id
    """)

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    data = []

    for row in resultado:
        data.append({
            "id": row[0],
            "nombre": row[1],
            "apellido": row[2],
            "documento": row[3],
            "email": row[4],
            "telefono": row[5],
            "sueldo": row[6]
        })

    return data

def obtener_profesores_paginado_controller(limit=50, offset=0, busqueda=None):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        filtros = []
        params = []

        if busqueda:
            filtros.append("""(
                LOWER(nombre || ' ' || apellido) LIKE LOWER(%s)
                OR LOWER(COALESCE(email, '')) LIKE LOWER(%s)
                OR LOWER(COALESCE(documento_identidad, '')) LIKE LOWER(%s)
            )""")
            patron = f"%{busqueda}%"
            params.extend([patron, patron, patron])

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"SELECT COUNT(*) FROM profesor {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, nombre, apellido, documento_identidad, email, telefono, sueldo
            FROM profesor
            {where_sql}
            ORDER BY id
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        resultado = cursor.fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [
                {
                    "id": row[0],
                    "nombre": row[1],
                    "apellido": row[2],
                    "documento": row[3],
                    "email": row[4],
                    "telefono": row[5],
                    "sueldo": row[6]
                }
                for row in resultado
            ]
        }
    finally:
        cursor.close()
        conn.close()

def obtener_clases_profesor_controller(profesor_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            a.id,
            c.nombre AS curso,
            m.nombre AS materia
        FROM asignaciones a
        JOIN cursos c ON c.id = a.curso_id
        JOIN materias m ON m.id = a.materia_id
        WHERE a.profesor_id = %s
    """, (profesor_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "asignacion_id": r[0],
            "curso": r[1],
            "materia": r[2]
        }
        for r in rows
    ]
def actualizar_profesor_controller(profesor_id, profesor):
    conn = get_connection()
    cursor = conn.cursor()

    if profesor.password:
        cursor.execute('''
            UPDATE profesor
            SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, telefono = %s, password = %s, sueldo = %s
            WHERE id = %s
        ''', (profesor.nombre, profesor.apellido, profesor.documento_identidad, profesor.email, profesor.telefono, get_password_hash(profesor.password), profesor.sueldo, profesor_id))
    else:
        cursor.execute('''
            UPDATE profesor 
            SET nombre = %s, apellido = %s, documento_identidad = %s, email = %s, telefono = %s, sueldo = %s
            WHERE id = %s
        ''', (profesor.nombre, profesor.apellido, profesor.documento_identidad, profesor.email, profesor.telefono, profesor.sueldo, profesor_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Profesor actualizado correctamente"}
