"""Persistencia del dominio ``planilla``, extraida en la subcapa 7.1.

Cada funcion recibe el cursor que ya abrio quien la llama y ejecuta una sola
sentencia. Este modulo no abre, cierra, confirma ni revierte recursos: los dos
controladores y el servicio conservan la propiedad de sus conexiones,
transacciones, resolucion de asignaciones, validaciones, calculos y payloads.

Las cinco cadenas SQL conservan su texto original. Tambien se conservan sus
parametros, retornos y orden de ejecucion, incluidos el reemplazo transaccional
de una nota y la conexion separada que usa la validacion del servicio.
"""


def borrar_nota_existente(
    cursor,
    estudiante_id,
    asignacion_id,
    periodo,
    descripcion,
):
    """Borra una nota con la misma clave logica antes de reemplazarla."""
    cursor.execute("""
            DELETE FROM notas_detalle
            WHERE estudiante_id = %s AND asignacion_id = %s AND periodo = %s AND LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))
        """, (estudiante_id, asignacion_id, periodo, descripcion))


def insertar_nota(
    cursor,
    estudiante_id,
    asignacion_id,
    periodo,
    nota,
    descripcion,
    tipo_evaluacion,
    valoracion,
):
    """Inserta la nota de planilla y devuelve su identificador."""
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
        estudiante_id,
        asignacion_id,
        periodo,
        nota,
        descripcion,
        tipo_evaluacion,
        valoracion
    ))
    return cursor.fetchone()[0]


def eliminar_tipo(cursor, asignacion_id, periodo, descripcion):
    """Elimina una descripcion de nota de toda la asignacion y periodo."""
    cursor.execute("""
            DELETE FROM notas_detalle
            WHERE asignacion_id = %s AND periodo = %s
            AND LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))
        """, (asignacion_id, periodo, descripcion))


def leer_filas_de_planilla(cursor, periodo, asignacion_id):
    """Devuelve las filas con las que el controlador arma el JSON actual."""
    cursor.execute("""
            SELECT
                e.id,
                e.nombre,
                e.apellido,
                m.nombre AS materia,
                nd.descripcion,
                nd.nota,
                COALESCE(nd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                nd.valoracion

            FROM asignaciones a
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            JOIN estudiantes e ON e.curso_id = a.curso_id

            LEFT JOIN notas_detalle nd
                ON nd.estudiante_id = e.id
                AND nd.asignacion_id = a.id
                AND nd.periodo = %s

            WHERE a.id = %s
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
        """, (periodo, asignacion_id))
    return cursor.fetchall()


def buscar_estudiante_en_asignacion(cursor, estudiante_id, asignacion_id):
    """Devuelve la fila testigo de pertenencia usada por la validacion."""
    cursor.execute("""
            SELECT e.id
            FROM estudiantes e
            JOIN asignaciones a ON e.curso_id = a.curso_id
            WHERE e.id = %s AND a.id = %s
        """, (estudiante_id, asignacion_id))
    return cursor.fetchone()
