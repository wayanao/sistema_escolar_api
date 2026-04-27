from app.database import get_connection

def obtener_inasistencias_profesor_controller(profesor_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.nombre || ' ' || e.apellido as nombre_estudiante,
            c.nombre as curso,
            COUNT(a.id) as total_fallas
        FROM asistencia a
        JOIN estudiantes e ON a.estudiante_id = e.id
        JOIN asignaciones asi ON a.asignacion_id = asi.id
        JOIN cursos c ON asi.curso_id = c.id
        WHERE asi.profesor_id = %s AND a.estado ILIKE 'ausente'
        GROUP BY e.id, e.nombre, e.apellido, c.nombre
        ORDER BY total_fallas DESC
        LIMIT 1
    """, (profesor_id,))

    resultado = cursor.fetchone()

    cursor.close()
    conn.close()

    if resultado:
        return {
            "nombre": resultado[0],
            "curso": resultado[1],
            "total_fallas": resultado[2]
        }
    return None

def obtener_notas_bajas_profesor_controller(profesor_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        WITH PromediosPorClase AS (
            SELECT
                e.id as estudiante_id,
                e.nombre,
                e.apellido,
                AVG(CAST(n.nota AS numeric)) as promedio_clase
            FROM notas_detalle n
            JOIN estudiantes e ON n.estudiante_id = e.id
            JOIN asignaciones asi ON n.asignacion_id = asi.id
            WHERE asi.profesor_id = %s
            GROUP BY e.id, e.nombre, e.apellido, asi.id
        )
        SELECT
            nombre || ' ' || apellido as nombre_estudiante,
            'Global (Varias clases)' as curso,
            TRUNC(AVG(promedio_clase), 2) as promedio
        FROM PromediosPorClase
        GROUP BY estudiante_id, nombre, apellido
        HAVING TRUNC(AVG(promedio_clase), 2) < 3.0
        ORDER BY promedio ASC
        LIMIT 1
    """, (profesor_id,))

    resultados = cursor.fetchall()

    cursor.close()
    conn.close()

    notas_bajas = []
    for row in resultados:
        promedio = float(row[2])
        color = "red" if promedio < 3.0 else "yellow" if promedio <= 3.5 else "green"
        notas_bajas.append({
            "nombre": row[0],
            "curso": row[1],
            "promedio": promedio,
            "color": color
        })

    return notas_bajas

def obtener_ranking_rendimiento_controller(asignacion_id, periodo):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.id as estudiante_id,
            e.nombre || ' ' || e.apellido as nombre_estudiante,
            TRUNC(AVG(CAST(n.nota AS numeric)), 2) as promedio
        FROM notas_detalle n
        JOIN estudiantes e ON n.estudiante_id = e.id
        WHERE n.asignacion_id = %s AND n.periodo = %s
        GROUP BY e.id, e.nombre, e.apellido
        HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) < 3.0
        ORDER BY promedio ASC
    """, (asignacion_id, periodo))

    resultados = cursor.fetchall()
    
    cursor.close()
    conn.close()

    ranking = []
    for row in resultados:
        ranking.append({
            "id": row[0],
            "nombre": row[1],
            "promedio": float(row[2])
        })

    return ranking

def obtener_notas_altas_profesor_controller(profesor_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        WITH PromediosPorClase AS (
            SELECT
                e.id as estudiante_id,
                e.nombre,
                e.apellido,
                AVG(CAST(n.nota AS numeric)) as promedio_clase
            FROM notas_detalle n
            JOIN estudiantes e ON n.estudiante_id = e.id
            JOIN asignaciones asi ON n.asignacion_id = asi.id
            WHERE asi.profesor_id = %s
            GROUP BY e.id, e.nombre, e.apellido, asi.id
        )
        SELECT
            nombre || ' ' || apellido as nombre_estudiante,
            'Global (Varias clases)' as curso,
            TRUNC(AVG(promedio_clase), 2) as promedio
        FROM PromediosPorClase
        GROUP BY estudiante_id, nombre, apellido
        HAVING TRUNC(AVG(promedio_clase), 2) >= 3.0
        ORDER BY promedio DESC
        LIMIT 1
    """, (profesor_id,))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    notas_altas = []
    for row in resultados:
        promedio = float(row[2])
        notas_altas.append({
            "nombre": row[0],
            "curso": row[1],
            "promedio": promedio,
            "color": "green"
        })

    return notas_altas

def obtener_ranking_mejor_rendimiento_controller(asignacion_id, periodo):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.id as estudiante_id,
            e.nombre || ' ' || e.apellido as nombre_estudiante,
            TRUNC(AVG(CAST(n.nota AS numeric)), 2) as promedio
        FROM notas_detalle n
        JOIN estudiantes e ON n.estudiante_id = e.id
        WHERE n.asignacion_id = %s AND n.periodo = %s
        GROUP BY e.id, e.nombre, e.apellido
        HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) >= 3.0
        ORDER BY promedio DESC
    """, (asignacion_id, periodo))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    ranking = []
    for row in resultados:
        ranking.append({
            "id": row[0],
            "nombre": row[1],
            "promedio": float(row[2])
        })

    return ranking