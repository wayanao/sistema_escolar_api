from app.database import get_connection
from app.services.planilla_service import validar_estudiante_asignacion


# 🎯 Registrar nota desde planilla
def registrar_nota_planilla_controller(data):

    # 🔥 VALIDACIÓN
    if not validar_estudiante_asignacion(data.estudiante_id, data.asignacion_id):
        return {"error": "El estudiante no pertenece a esta asignación"}

    conn = get_connection()
    cursor = conn.cursor()
    tipo_evaluacion = getattr(data, "tipo_evaluacion", "numerica") or "numerica"
    nota = data.nota if tipo_evaluacion == "numerica" else None
    valoracion = getattr(data, "valoracion", None) if tipo_evaluacion == "desarrollo" else None

    # 🔥 Evitar duplicados: Primero eliminamos si ya existe la nota para ese tipo, luego insertamos
    cursor.execute("""
        DELETE FROM notas_detalle
        WHERE estudiante_id = %s AND asignacion_id = %s AND periodo = %s AND LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))
    """, (data.estudiante_id, data.asignacion_id, data.periodo, data.descripcion))

    cursor.execute("""
        INSERT INTO notas_detalle (
            estudiante_id,
            asignacion_id,
            periodo,
            nota,
            descripcion,
            tipo_evaluacion,
            valoracion
        )
        VALUES (%s, %s, %s, %s, TRIM(%s), %s, %s)
        RETURNING id
    """, (
        data.estudiante_id,
        data.asignacion_id,
        data.periodo,
        nota,
        data.descripcion,
        tipo_evaluacion,
        valoracion
    ))

    nota_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "mensaje": "Nota registrada correctamente",
        "nota_id": nota_id
    }


# 🔥 eliminar tipo (columna)

def eliminar_tipo_controller(asignacion_id, descripcion, periodo: int = 1):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM notas_detalle
        WHERE asignacion_id = %s AND periodo = %s
        AND LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))
    """, (asignacion_id, periodo, descripcion))

    conn.commit()

    cursor.close()
    conn.close()

    return {"mensaje": "Tipo eliminado correctamente"}
