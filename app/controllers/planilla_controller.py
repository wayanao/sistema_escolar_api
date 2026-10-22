from app.core.nivel_academico import resolver_tipo_evaluacion
from app.database import get_cursor
from app.repositories import (
    planilla_repository,
    porcentajes_planilla_repository,
    subnotas_planilla_repository,
)
from app.services.anio_lectivo import exigir_asignacion_editable
from app.services.asignacion_academica import (
    resolver_asignacion_academica_id_cursor,
    resolver_nivel_curso_cursor,
)
from app.services.planilla_service import validar_estudiante_asignacion


NOTA_CALCULADA = "Esta nota se calcula con sus subnotas. Cámbiala desde las subnotas."


class NotaCalculadaError(Exception):
    """La celda tiene subnotas calificadas y no se escribe a mano (P1 de
    docs/funcionalidades/SUBNOTAS_PLANILLA.md). La ruta lo traduce a 409."""


# 🎯 Registrar nota desde planilla
def registrar_nota_planilla_controller(data, *, usuario):

    with get_cursor(commit=True) as cursor:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_asignacion_editable(cursor, data.asignacion_id, usuario)

        # 🔥 VALIDACIÓN
        # Sobre el cursor que este bloque ya abrio: antes pedia una conexion
        # propia al pool solo para esta consulta.
        if not validar_estudiante_asignacion(
            data.estudiante_id,
            data.asignacion_id,
            cursor=cursor,
        ):
            return {"error": "El estudiante no pertenece a esta asignación"}

        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, data.asignacion_id)
        nivel_curso = resolver_nivel_curso_cursor(cursor, asignacion_id)
        tipo_evaluacion = resolver_tipo_evaluacion(
            nivel_curso, getattr(data, "tipo_evaluacion", None)
        )
        nota = data.nota if tipo_evaluacion == "numerica" else None
        valoracion = getattr(data, "valoracion", None) if tipo_evaluacion == "desarrollo" else None

        # Subnotas, paso A1: una celda con subnotas calificadas es su promedio
        # y no se escribe a mano. Una consulta mas en la misma conexion; sin
        # subnotas, lo de abajo es exactamente lo de siempre.
        if subnotas_planilla_repository.hay_subnotas_calificadas(
            cursor,
            asignacion_id,
            data.periodo,
            data.descripcion,
            data.estudiante_id,
        ):
            raise NotaCalculadaError(NOTA_CALCULADA)

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

def eliminar_tipo_controller(asignacion_id, descripcion, periodo: int = 1, *, usuario):

    with get_cursor(commit=True) as cursor:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_asignacion_editable(cursor, asignacion_id, usuario)
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

        planilla_repository.eliminar_tipo(
            cursor,
            asignacion_id,
            periodo,
            descripcion,
        )
        # Subnotas, paso A1 (P6): el tipo se lleva sus subnotas en la misma
        # transaccion. Si no, reaparecerian al crear otro con el mismo nombre.
        subnotas_planilla_repository.eliminar_subnotas_del_tipo(
            cursor,
            asignacion_id,
            periodo,
            descripcion,
        )
        # Porcentajes, paso B2b (PB10): y su porcentaje, por el mismo motivo.
        porcentajes_planilla_repository.quitar_porcentaje(
            cursor,
            asignacion_id,
            periodo,
            descripcion,
        )

    return {"mensaje": "Tipo eliminado correctamente"}
