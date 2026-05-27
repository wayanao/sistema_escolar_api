from app.database import get_connection


def _title_case_es(value):
    return " ".join(
        word[:1].upper() + word[1:].lower()
        for word in str(value or "").strip().split()
    )


# 🎯 Crear curso
def crear_curso_controller(curso):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cursos (nombre, jornada)
        VALUES (%s, %s)
        RETURNING id
    """, (
        _title_case_es(curso.nombre),
        curso.jornada
    ))

    curso_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return curso_id 


# 🎯 Listar cursos
def obtener_cursos_controller():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nombre, jornada
        FROM cursos
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
            "jornada": row[2] or "Mañana"
        })

    return data

def obtener_cursos_paginado_controller(limit=50, offset=0, busqueda=None):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        filtros = []
        params = []

        if busqueda:
            filtros.append("LOWER(nombre) LIKE LOWER(%s)")
            params.append(f"%{busqueda}%")

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"SELECT COUNT(*) FROM cursos {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, nombre, jornada
            FROM cursos
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
                    "jornada": row[2] or "Mañana"
                }
                for row in resultado
            ]
        }
    finally:
        cursor.close()
        conn.close()

def actualizar_curso_controller(curso_id, curso):
    from app.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE cursos
        SET nombre = %s, jornada = %s
        WHERE id = %s
    ''', (_title_case_es(curso.nombre), curso.jornada, curso_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Curso actualizado correctamente"}
