"""Persistencia del dominio ``planilla``, extraida en la subcapa 7.1.

Cada funcion recibe el cursor que ya abrio quien la llama y ejecuta una sola
sentencia. Este modulo no abre, cierra, confirma ni revierte recursos: los dos
controladores y el servicio conservan la propiedad de sus conexiones,
transacciones, resolucion de asignaciones, validaciones, calculos y payloads.

Las cinco cadenas SQL conservan su texto original. Tambien se conservan sus
parametros, retornos y orden de ejecucion, incluidos el reemplazo transaccional
de una nota y la conexion separada que usa la validacion del servicio.

Excepcion: ``leer_filas_de_planilla`` ahora tambien selecciona ``nd.id``, para
que el controlador pueda ordenar las columnas de planilla por orden de
creacion en vez de alfabeticamente (pedido explicito del usuario).

Cambiar una nota ya **no la borra y la vuelve a crear** (2026-11-23):
``actualizar_nota_existente`` cambia la misma fila y conserva su ``id``. Con
borrar e insertar, la nota cambiada recibia un ``id`` nuevo y pasaba al final:
Boletin final ordena las tarjetas por ``nd.id`` y empareja los textos
guardados por posicion, asi que los textos se corrian una tarjeta. Solo una
nota que no existia se inserta (``insertar_nota``).
"""


def actualizar_nota_existente(
    cursor,
    estudiante_id,
    asignacion_id,
    periodo,
    nota,
    descripcion,
    tipo_evaluacion,
    valoracion,
):
    """Cambia la nota con esa clave logica sin cambiarle el ``id``.

    Devuelve su ``id``, o ``None`` si no habia ninguna (entonces se inserta).
    Si hubiera repetidas, cambia la mas antigua, la que tiene el lugar de la
    tarjeta; ``borrar_notas_repetidas`` quita las demas. La descripcion queda
    como llega, recortada, igual que al insertar.
    """
    cursor.execute("""
            UPDATE notas_detalle
            SET nota = %s, descripcion = TRIM(%s), tipo_evaluacion = %s, valoracion = %s
            WHERE id = (
                SELECT MIN(id) FROM notas_detalle
                WHERE estudiante_id = %s AND asignacion_id = %s AND periodo = %s AND LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))
            )
            RETURNING id
        """, (
        nota,
        descripcion,
        tipo_evaluacion,
        valoracion,
        estudiante_id,
        asignacion_id,
        periodo,
        descripcion,
    ))
    fila = cursor.fetchone()
    return fila[0] if fila else None


def borrar_notas_repetidas(
    cursor,
    estudiante_id,
    asignacion_id,
    periodo,
    descripcion,
    conservar_id,
):
    """Borra las demas notas con la misma clave logica, menos ``conservar_id``.

    Antes las quitaba el borrado previo a insertar; asi sigue quedando una
    sola nota por estudiante, tipo y periodo.
    """
    cursor.execute("""
            DELETE FROM notas_detalle
            WHERE estudiante_id = %s AND asignacion_id = %s AND periodo = %s AND LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))
              AND id <> %s
        """, (estudiante_id, asignacion_id, periodo, descripcion, conservar_id))


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
                nd.valoracion,
                nd.id AS nota_id

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
