from app.database import get_cursor
from app.repositories import planilla_repository
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor
from app.services.planilla_service import validar_estudiante_asignacion


# 🎯 Registrar nota desde planilla
def registrar_nota_planilla_controller(data):

    # 🔥 VALIDACIÓN
    if not validar_estudiante_asignacion(data.estudiante_id, data.asignacion_id):
        return {"error": "El estudiante no pertenece a esta asignación"}

    with get_cursor(commit=True) as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, data.asignacion_id)
        tipo_evaluacion = getattr(data, "tipo_evaluacion", "numerica") or "numerica"
        nota = data.nota if tipo_evaluacion == "numerica" else None
        valoracion = getattr(data, "valoracion", None) if tipo_evaluacion == "desarrollo" else None

        # 🔥 Evitar duplicados: Primero eliminamos si ya existe la nota para ese tipo, luego insertamos
        planilla_repository.borrar_nota_existente(
            cursor,
            data.estudiante_id,
            asignacion_id,
            data.periodo,
            data.descripcion,
        )
        nota_id = planilla_repository.insertar_nota(
            cursor,
            data.estudiante_id,
            asignacion_id,
            data.periodo,
            nota,
            data.descripcion,
            tipo_evaluacion,
            valoracion,
        )

    return {
        "mensaje": "Nota registrada correctamente",
        "nota_id": nota_id
    }


# 🔥 eliminar tipo (columna)

def eliminar_tipo_controller(asignacion_id, descripcion, periodo: int = 1):

    with get_cursor(commit=True) as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

        planilla_repository.eliminar_tipo(
            cursor,
            asignacion_id,
            periodo,
            descripcion,
        )

    return {"mensaje": "Tipo eliminado correctamente"}
