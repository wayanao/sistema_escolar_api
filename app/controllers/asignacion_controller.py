from fastapi import HTTPException
from pydantic import BaseModel
from app.database import get_connection

# Umbral entre jornadas Mañana / Tarde (formato HH:MM 24h)
JORNADA_LIMITE = "12:00"


def validar_jornada_curso(cursor, curso_id, hora_inicio, hora_fin):
    """Devuelve un mensaje de error si la hora no respeta la jornada del curso,
    o None si todo está OK."""
    if not hora_inicio or not hora_fin:
        return None

    cursor.execute("SELECT jornada FROM cursos WHERE id = %s", (curso_id,))
    row = cursor.fetchone()
    if not row:
        return None  # el curso ya se valida por la FK en el INSERT

    jornada = (row[0] or "").strip().lower()
    if not jornada:
        return None  # curso sin jornada definida → no se valida

    if "mañan" in jornada or "manan" in jornada:
        if hora_fin > JORNADA_LIMITE:
            return f"El curso es jornada Mañana: la clase debe terminar antes o a las {JORNADA_LIMITE}."
    elif "tarde" in jornada:
        if hora_inicio < JORNADA_LIMITE:
            return f"El curso es jornada Tarde: la clase debe comenzar a partir de las {JORNADA_LIMITE}."

    return None


def verificar_cruce_horario(cursor, campo_id, valor_id, dia, hora_inicio_nueva, hora_fin_nueva):
    if not hora_inicio_nueva or not hora_fin_nueva:
        return False
        
    cursor.execute(f"SELECT hora_inicio, hora_fin FROM asignaciones WHERE {campo_id} = %s AND dia = %s", (valor_id, dia))
    registros = cursor.fetchall()
    
    for row in registros:
        h_inicio_db = row[0]
        h_fin_db = row[1]
        
        # Ignorar si están vacíos o nulos
        if not h_inicio_db or not h_fin_db or h_inicio_db.strip() == "" or h_fin_db.strip() == "":
            continue
            
        # Comparamos cadenas asumiendo formato HH:MM (ej. '07:00' < '08:30')
        # Esto funciona perfectamente para formatos de hora en 24h.
        if h_inicio_db < hora_fin_nueva and h_fin_db > hora_inicio_nueva:
            return True
            
    return False

# 🎯 Asignar profesor a curso
def asignar_profesor_controller(asignacion):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if asignacion.hora_inicio and asignacion.hora_fin:
            if asignacion.hora_inicio >= asignacion.hora_fin:
                return {"error": "La hora de inicio debe ser anterior a la hora de fin."}

            error_jornada = validar_jornada_curso(cursor, asignacion.curso_id, asignacion.hora_inicio, asignacion.hora_fin)
            if error_jornada:
                return {"error": error_jornada}

            if verificar_cruce_horario(cursor, "profesor_id", asignacion.profesor_id, asignacion.dia, asignacion.hora_inicio, asignacion.hora_fin):
                return {"error": "Error: El profesor ya tiene una clase asignada en ese horario y ese día."}

            if verificar_cruce_horario(cursor, "curso_id", asignacion.curso_id, asignacion.dia, asignacion.hora_inicio, asignacion.hora_fin):
                return {"error": "Error: El curso (salón) ya tiene otra clase asignada en ese horario y ese día."}

        cursor.execute("""
            INSERT INTO asignaciones (profesor_id, curso_id, materia_id, dia, hora_inicio, hora_fin)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            asignacion.profesor_id,
            asignacion.curso_id,
            asignacion.materia_id,
            asignacion.dia,
            asignacion.hora_inicio,
            asignacion.hora_fin
        ))

        asignacion_id = cursor.fetchone()[0]
        conn.commit()
        return {
            "mensaje": "Asignación creada",
            "id": asignacion_id
        }
    finally:
        cursor.close()
        conn.close()


# 🎯 Ver cursos de un profesor
def cursos_por_profesor_controller(profesor_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.id,
            c.nombre
        FROM asignaciones a
        JOIN cursos c ON a.curso_id = c.id
        WHERE a.profesor_id = %s
    """, (profesor_id,))

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    data = []

    for row in resultado:
        data.append({
            "curso_id": row[0],
            "nombre": row[1]
        })

    return data


# 🎯 Ver profesor de un curso
def profesor_por_curso_controller(curso_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            p.id,
            p.nombre,
            p.apellido
        FROM asignaciones a
        JOIN profesor p ON a.profesor_id = p.id
        WHERE a.curso_id = %s
    """, (curso_id,))

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    data = []

    for row in resultado:
        data.append({
            "profesor_id": row[0],
            "nombre": row[1],
            "apellido": row[2]
        })

    return data
def obtener_horarios_admin_controller():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            p.nombre || ' ' || p.apellido AS profesor,
            c.nombre AS curso,
            m.nombre AS materia,
            a.dia,
            a.hora_inicio,
            a.hora_fin
        FROM asignaciones a
        JOIN profesor p ON a.profesor_id = p.id
        JOIN cursos c ON a.curso_id = c.id
        JOIN materias m ON a.materia_id = m.id
        WHERE a.dia IS NOT NULL 
          AND a.hora_inicio IS NOT NULL 
          AND a.hora_fin IS NOT NULL
          AND a.hora_inicio != ''
          AND a.hora_fin != ''
        ORDER BY 
            CASE a.dia
                WHEN 'Lunes' THEN 1
                WHEN 'Martes' THEN 2
                WHEN 'Miércoles' THEN 3
                WHEN 'Jueves' THEN 4
                WHEN 'Viernes' THEN 5
                WHEN 'Sábado' THEN 6
                WHEN 'Domingo' THEN 7
                ELSE 8
            END,
            a.hora_inicio
    """)

    clases = cursor.fetchall()

    resultado = []
    for c in clases:
        resultado.append({
            "profesor": c[0],
            "curso": c[1],
            "materia": c[2],
            "dia": c[3],
            "hora_inicio": c[4],
            "hora_fin": c[5]
        })

    cursor.close()
    conn.close()

    return resultado

# 🎯 Eliminar asignación profesor ↔ curso
def eliminar_asignacion_controller(profesor_id, curso_id):

    conn = get_connection()
    cursor = conn.cursor()

    # 🔍 1. Obtener ID de la asignación
    cursor.execute("""
        SELECT id FROM asignaciones
        WHERE profesor_id = %s AND curso_id = %s
    """, (profesor_id, curso_id))

    asignacion = cursor.fetchone()

    if not asignacion:
        return {"mensaje": "Asignación no encontrada"}

    asignacion_id = asignacion[0]

    # ❌ 2. Eliminar notas relacionadas
    cursor.execute("""
        DELETE FROM notas
        WHERE asignacion_id = %s
    """, (asignacion_id,))

    # ❌ 3. Eliminar asignación
    cursor.execute("""
        DELETE FROM asignaciones
        WHERE id = %s
    """, (asignacion_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return {"mensaje": "Asignación eliminada junto con sus notas"}

def obtener_clases_profesor_controller(profesor_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            a.id,
            c.nombre,
            m.nombre
        FROM asignaciones a
        JOIN cursos c ON a.curso_id = c.id
        JOIN materias m ON a.materia_id = m.id
        WHERE a.profesor_id = %s
    """, (profesor_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id": r[0],
            "curso": r[1],
            "materia": r[2]
        }
        for r in rows
    ]
# ❌ Eliminar asignación por ID (más seguro para grilla)
def eliminar_asignacion_por_id_controller(asignacion_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM asignaciones WHERE id = %s", (asignacion_id,))
        if not cursor.fetchone():
            return {"error": "Asignación no encontrada"}

        cursor.execute("DELETE FROM notas WHERE asignacion_id = %s", (asignacion_id,))
        cursor.execute("DELETE FROM asignaciones WHERE id = %s", (asignacion_id,))
        conn.commit()
        return {"mensaje": "Asignación eliminada junto con sus notas"}
    finally:
        cursor.close()
        conn.close()


def verificar_cruce_horario_editar(cursor, campo_id, valor_id, dia, hora_inicio_nueva, hora_fin_nueva, asignacion_id_ignorar):
    if not hora_inicio_nueva or not hora_fin_nueva:
        return False

    cursor.execute(f"SELECT hora_inicio, hora_fin FROM asignaciones WHERE {campo_id} = %s AND dia = %s AND id != %s", (valor_id, dia, asignacion_id_ignorar))
    registros = cursor.fetchall()

    for row in registros:
        h_inicio_db = row[0]
        h_fin_db = row[1]

        if not h_inicio_db or not h_fin_db or h_inicio_db.strip() == "" or h_fin_db.strip() == "":
            continue

        if h_inicio_db < hora_fin_nueva and h_fin_db > hora_inicio_nueva:       
            return True
            
    return False

def editar_asignacion_controller(asignacion_id, asignacion):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if asignacion.hora_inicio and asignacion.hora_fin:
            if asignacion.hora_inicio >= asignacion.hora_fin:
                return {"error": "La hora de inicio debe ser anterior a la hora de fin."}

            error_jornada = validar_jornada_curso(cursor, asignacion.curso_id, asignacion.hora_inicio, asignacion.hora_fin)
            if error_jornada:
                return {"error": error_jornada}

            if verificar_cruce_horario_editar(cursor, "profesor_id", asignacion.profesor_id, asignacion.dia, asignacion.hora_inicio, asignacion.hora_fin, asignacion_id):
                return {"error": "Error: El profesor ya tiene una clase asignada en ese horario y ese día."}

            if verificar_cruce_horario_editar(cursor, "curso_id", asignacion.curso_id, asignacion.dia, asignacion.hora_inicio, asignacion.hora_fin, asignacion_id):
                return {"error": "Error: El curso (salón) ya tiene otra clase asignada en ese horario y ese día."}

        cursor.execute("""
            UPDATE asignaciones
            SET profesor_id = %s, curso_id = %s, materia_id = %s, dia = %s, hora_inicio = %s, hora_fin = %s
            WHERE id = %s
            RETURNING id
        """, (
            asignacion.profesor_id,
            asignacion.curso_id,
            asignacion.materia_id,
            asignacion.dia,
            asignacion.hora_inicio,
            asignacion.hora_fin,
            asignacion_id
        ))

        res = cursor.fetchone()
        if not res:
            return {"error": "Asignación no encontrada"}
            
        conn.commit()
        return {
            "mensaje": "Asignación actualizada"
        }
    finally:
        cursor.close()
        conn.close()

def obtener_todas_asignaciones_controller():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            a.id, a.profesor_id, a.curso_id, a.materia_id, a.dia, a.hora_inicio, a.hora_fin,
            p.nombre || ' ' || p.apellido AS profesor_nombre,
            c.nombre AS curso_nombre,
            m.nombre AS materia_nombre
        FROM asignaciones a
        JOIN profesor p ON a.profesor_id = p.id
        JOIN cursos c ON a.curso_id = c.id
        JOIN materias m ON a.materia_id = m.id
        ORDER BY a.id DESC
    """)

    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    resultado = []
    for r in rows:
        resultado.append({
            "id": r[0],
            "profesor_id": r[1],
            "curso_id": r[2],
            "materia_id": r[3],
            "dia": r[4] or "",
            "hora_inicio": r[5] or "",
            "hora_fin": r[6] or "",
            "profesor_nombre": r[7],
            "curso_nombre": r[8],
            "materia_nombre": r[9]
        })
        
    return resultado
