from app.database import get_cursor
from app.repositories import planilla_repository


# 🎯 Validar que el estudiante pertenece a la asignación
def validar_estudiante_asignacion(estudiante_id, asignacion_id):

    with get_cursor() as cursor:
        existe = planilla_repository.buscar_estudiante_en_asignacion(
            cursor,
            estudiante_id,
            asignacion_id,
        )

    return existe is not None
