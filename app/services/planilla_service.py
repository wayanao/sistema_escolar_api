from app.database import get_cursor
from app.repositories import planilla_repository


# 🎯 Validar que el estudiante pertenece a la asignación
def validar_estudiante_asignacion(estudiante_id, asignacion_id, *, cursor=None):
    """El estudiante pertenece al curso de la asignacion.

    `cursor` es opcional y replica el que ya aceptan las funciones de
    `app/core/permissions.py`: quien ya tiene una conexion abierta presta su
    cursor y se ahorra pedir otra al pool. Contra Neon cada ida y vuelta cuesta
    ~180 ms, y cada conexion nueva paga dos antes de consultar nada. Sin
    `cursor` abre y cierra la suya, que es el comportamiento historico.

    Prestar el cursor **no relaja la validacion**: es la misma consulta con los
    mismos parametros, y el rechazo se devuelve igual.
    """
    if cursor is not None:
        return planilla_repository.buscar_estudiante_en_asignacion(
            cursor,
            estudiante_id,
            asignacion_id,
        ) is not None

    with get_cursor() as cursor_propio:
        existe = planilla_repository.buscar_estudiante_en_asignacion(
            cursor_propio,
            estudiante_id,
            asignacion_id,
        )

    return existe is not None


def guardar_celda(
    cursor, estudiante_id, asignacion_id, periodo, nota, descripcion, tipo_evaluacion, valoracion
):
    """Escribe la celda de un estudiante y devuelve el `id` de su nota.

    Si ya existia, la cambia en su lugar y quita las repetidas; si no, la
    inserta. Son dos sentencias, como el par borrar/insertar de antes, en la
    transaccion de quien llama. Conservar el `id` es lo que evita que la
    tarjeta se mueva en Boletin final (2026-11-23). La usan el guardado a mano
    (`planilla_controller`) y el de subnotas (`subnotas_planilla_controller`).
    """
    nota_id = planilla_repository.actualizar_nota_existente(
        cursor, estudiante_id, asignacion_id, periodo, nota, descripcion, tipo_evaluacion, valoracion
    )
    if nota_id is None:
        return planilla_repository.insertar_nota(
            cursor, estudiante_id, asignacion_id, periodo, nota, descripcion, tipo_evaluacion, valoracion
        )
    planilla_repository.borrar_notas_repetidas(
        cursor, estudiante_id, asignacion_id, periodo, descripcion, nota_id
    )
    return nota_id
