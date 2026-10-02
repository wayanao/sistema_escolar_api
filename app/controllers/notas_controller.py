from app.database import get_cursor
from app.repositories import notas_repository
from app.services.anio_lectivo import exigir_asignacion_editable
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor

# 👇 IMPORTAMOS SERVICES
from app.services.nota_service import (
    validar_asignacion,
    validar_estudiante,
    validar_estudiante_en_curso
)


# 🎯 Crear nota
def crear_nota_controller(nota, *, usuario):

    # 🔥 VALIDACIONES (SERVICE)
    if not validar_asignacion(nota.asignacion_id):
        return {"error": "La asignación no existe"}

    if not validar_estudiante(nota.estudiante_id):
        return {"error": "El estudiante no existe"}

    if not validar_estudiante_en_curso(nota.estudiante_id, nota.asignacion_id):
        return {"error": "El estudiante no pertenece a ese curso"}

    # 🔌 conexión
    with get_cursor(commit=True) as cursor:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_asignacion_editable(cursor, nota.asignacion_id, usuario)
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, nota.asignacion_id)

        # 🧠 Insertar nota
        nota_id = notas_repository.insertar_nota(
            cursor,
            nota.estudiante_id,
            asignacion_id,
            nota.nota,
            nota.descripcion
        )

    return {"mensaje": "Nota creada", "id": nota_id}


# 🎯 Obtener notas por estudiante + promedio
def notas_estudiante_controller(estudiante_id):

    with get_cursor() as cursor:
        resultado = notas_repository.leer_notas_de_estudiante(cursor, estudiante_id)

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
        resultado = notas_repository.leer_boletin_de_estudiante(cursor, estudiante_id)

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

        resultado = notas_repository.leer_planilla_de_asignacion(cursor, asignacion_id)

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
        asignaciones_estudiante = notas_repository.leer_asignaciones_del_estudiante(
            cursor, estudiante_id
        )

        if not asignaciones_estudiante:
            return []

        materias_resultado = []

        for asig in asignaciones_estudiante:
            materia_id, nombre_area, docente_nombre, asignacion_id = asig

            # Obtener las notas_detalle guardadas para este estudiante y asignacion, en este periodo
            notas = notas_repository.leer_notas_de_asignacion_en_periodo(
                cursor, estudiante_id, asignacion_id, periodo
            )

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

