from app.database import get_connection


def _title_case_es(value):
    return " ".join(
        word[:1].upper() + word[1:].lower()
        for word in str(value or "").strip().split()
    )


def crear_materia_controller(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO materias (nombre)
        VALUES (%s)
    """, (_title_case_es(data["nombre"]),))

    conn.commit()

    cursor.close()
    conn.close()

    return {"mensaje": "Materia creada"}



def obtener_materias_controller():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nombre FROM materias
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id": r[0],
            "nombre": r[1]
        }
        for r in rows
    ]

def obtener_materias_paginado_controller(limit=50, offset=0, busqueda=None):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        filtros = []
        params = []

        if busqueda:
            filtros.append("LOWER(nombre) LIKE LOWER(%s)")
            params.append(f"%{busqueda}%")

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"SELECT COUNT(*) FROM materias {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, nombre
            FROM materias
            {where_sql}
            ORDER BY id
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        rows = cursor.fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [
                {
                    "id": r[0],
                    "nombre": r[1]
                }
                for r in rows
            ]
        }
    finally:
        cursor.close()
        conn.close()

def actualizar_materia_controller(materia_id, data):
    from app.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE materias
        SET nombre = %s
        WHERE id = %s
    ''', (_title_case_es(data["nombre"]), materia_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Materia actualizada correctamente"}
