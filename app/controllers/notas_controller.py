from app.database import get_cursor
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor

# 👇 IMPORTAMOS SERVICES
from app.services.nota_service import (
    validar_asignacion,
    validar_estudiante,
    validar_estudiante_en_curso
)


# 🎯 Crear nota
def crear_nota_controller(nota):

    # 🔥 VALIDACIONES (SERVICE)
    if not validar_asignacion(nota.asignacion_id):
        return {"error": "La asignación no existe"}

    if not validar_estudiante(nota.estudiante_id):
        return {"error": "El estudiante no existe"}

    if not validar_estudiante_en_curso(nota.estudiante_id, nota.asignacion_id):
        return {"error": "El estudiante no pertenece a ese curso"}

    # 🔌 conexión
    with get_cursor(commit=True) as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, nota.asignacion_id)

        # 🧠 Insertar nota
        cursor.execute("""
            INSERT INTO notas_detalle (
                estudiante_id,
                asignacion_id,
                nota,
                descripcion
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            nota.estudiante_id,
            asignacion_id,
            nota.nota,
            nota.descripcion
        ))

        nota_id = cursor.fetchone()[0]

    return {"mensaje": "Nota creada", "id": nota_id}


# 🎯 Obtener notas por estudiante + promedio
def notas_estudiante_controller(estudiante_id):

    with get_cursor() as cursor:
        cursor.execute("""
            SELECT
                nd.nota,
                nd.descripcion
            FROM notas_detalle nd
            WHERE nd.estudiante_id = %s
        """, (estudiante_id,))

        resultado = cursor.fetchall()

    # 📊 Calcular promedio
    total = 0
    cantidad = len(resultado)

    data = []

    for row in resultado:
        total += float(row[0])

        data.append({
            "nota": float(row[0]),
            "descripcion": row[1]
        })

    promedio = total / cantidad if cantidad > 0 else 0

    return {
        "notas": data,
        "promedio": round(promedio, 2)
    }

def boletin_estudiante_controller(estudiante_id):

    with get_cursor() as cursor:
        cursor.execute("""
            WITH asignaciones_academicas AS (
                SELECT DISTINCT ON (COALESCE(a.asignacion_academica_id, a.id))
                    COALESCE(a.asignacion_academica_id, a.id) AS id,
                    a.curso_id,
                    a.materia_id,
                    COALESCE(a.orden_boletin, 100) AS orden_boletin
                FROM asignaciones a
                WHERE a.activo = TRUE
                ORDER BY COALESCE(a.asignacion_academica_id, a.id), COALESCE(a.orden_boletin, 100), a.id
            )
            SELECT
                e.nombre,
                e.apellido,
                c.nombre AS curso,
                m.nombre AS materia,
                COALESCE(AVG(nd.nota), 0) AS promedio_materia

            FROM estudiantes e
            JOIN cursos c ON e.curso_id = c.id
            JOIN asignaciones_academicas a ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id

            LEFT JOIN notas_detalle nd
                ON nd.estudiante_id = e.id
                AND nd.asignacion_id = a.id

            WHERE e.id = %s

            GROUP BY e.nombre, e.apellido, c.nombre, m.nombre, a.orden_boletin
            ORDER BY a.orden_boletin, m.nombre
        """, (estudiante_id,))

        resultado = cursor.fetchall()

    if not resultado:
        return {"mensaje": "Estudiante no encontrado"}

    materias = []
    total = 0

    for row in resultado:
        promedio = float(row[4])

        materias.append({
            "materia": row[3],
            "promedio": round(promedio, 2),
            "estado": "Aprobado" if promedio >= 3 else "Reprobado"
        })

        total += promedio

    promedio_general = total / len(materias)

    return {
        "nombre": resultado[0][0],
        "apellido": resultado[0][1],
        "curso": resultado[0][2],
        "materias": materias,
        "promedio_general": round(promedio_general, 2),
        "estado_final": "Aprobado" if promedio_general >= 3 else "Reprobado"
    }

    # 🎯 Planilla por asignación (PRO)
def planilla_asignacion_controller(asignacion_id):

    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

        cursor.execute("""
            SELECT
                e.id,
                e.nombre,
                e.apellido,
                m.nombre AS materia,
                c.nombre AS curso,
                COALESCE(AVG(nd.nota), 0) AS promedio

            FROM asignaciones a

            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            JOIN estudiantes e ON e.curso_id = c.id

            LEFT JOIN notas_detalle nd
                ON nd.estudiante_id = e.id
                AND nd.asignacion_id = a.id

            WHERE a.id = %s
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'

            GROUP BY e.id, e.nombre, e.apellido, m.nombre, c.nombre
            ORDER BY e.nombre
        """, (asignacion_id,))

        resultado = cursor.fetchall()

    data = []

    for row in resultado:
        data.append({
            "estudiante_id": row[0],
            "nombre": row[1],
            "apellido": row[2],
            "materia": row[3],
            "curso": row[4],
            "promedio": round(float(row[5]), 2)
        })

    return data

def boletin_detallado_controller(estudiante_id, periodo=1):
    with get_cursor() as cursor:
        # Obtener todas las materias asignadas al curso del estudiante
        cursor.execute("""
            WITH asignaciones_academicas AS (
                SELECT DISTINCT ON (COALESCE(a.asignacion_academica_id, a.id))
                    COALESCE(a.asignacion_academica_id, a.id) AS id,
                    a.curso_id,
                    a.materia_id,
                    a.profesor_id,
                    COALESCE(a.orden_boletin, 100) AS orden_boletin
                FROM asignaciones a
                WHERE a.activo = TRUE
                ORDER BY COALESCE(a.asignacion_academica_id, a.id), COALESCE(a.orden_boletin, 100), a.id
            )
            SELECT
                m.id,
                m.nombre AS area,
                p.nombre || ' ' || p.apellido AS docente,
                a.id AS asignacion_id
            FROM estudiantes e
            JOIN cursos c ON e.curso_id = c.id
            JOIN asignaciones_academicas a ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            JOIN profesor p ON a.profesor_id = p.id
            WHERE e.id = %s
            ORDER BY a.orden_boletin, m.nombre
        """, (estudiante_id,))
        asignaciones_estudiante = cursor.fetchall()

        if not asignaciones_estudiante:
            return []

        materias_resultado = []

        for asig in asignaciones_estudiante:
            materia_id, nombre_area, docente_nombre, asignacion_id = asig

            # Obtener las notas_detalle guardadas para este estudiante y asignacion, en este periodo
            cursor.execute("""
                SELECT id, descripcion, nota
                FROM notas_detalle
                WHERE estudiante_id = %s AND asignacion_id = %s AND periodo = %s
                ORDER BY id ASC
            """, (estudiante_id, asignacion_id, periodo))
            notas = cursor.fetchall()

            actividades = []
            if notas:
                for nd in notas:
                    actividades.append({
                        "id": nd[0],
                        "descripcion": nd[1],
                        "nota": float(nd[2])
                    })
            else:
                # Si no hay calificaciones, inicializamos 3 espacios en blanco para el Boletín
                actividades = [
                    { "id": int(str(materia_id) + "01"), "descripcion": "Actividad 1", "nota": 0.0 },
                    { "id": int(str(materia_id) + "02"), "descripcion": "Actividad 2", "nota": 0.0 },
                    { "id": int(str(materia_id) + "03"), "descripcion": "Actividad 3", "nota": 0.0 }
                ]

            materias_resultado.append({
                "id": materia_id,
                "asignacion_id": asignacion_id,
                "area": nombre_area,
                "docente": docente_nombre,
                "actividades": actividades,
                "promedio": 0  # El frontend recalcula luego
            })

    return materias_resultado

