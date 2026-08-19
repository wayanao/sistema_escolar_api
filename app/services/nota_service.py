from app.database import get_cursor
from app.repositories import notas_repository


# 🎯 Validar que la asignación existe
def validar_asignacion(asignacion_id):

    with get_cursor() as cursor:
        existe = notas_repository.buscar_asignacion(cursor, asignacion_id)

    return existe is not None


# 🎯 Validar que el estudiante existe
def validar_estudiante(estudiante_id):

    with get_cursor() as cursor:
        existe = notas_repository.buscar_estudiante(cursor, estudiante_id)

    return existe is not None


# 🎯 Validar que el estudiante pertenece al curso de la asignación (PRO 🔥)
def validar_estudiante_en_curso(estudiante_id, asignacion_id):

    with get_cursor() as cursor:
        existe = notas_repository.buscar_estudiante_en_curso_de_asignacion(
            cursor, estudiante_id, asignacion_id
        )

    return existe is not None
