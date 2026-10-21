"""Consultas de `planilla_subnotas` y `planilla_subnotas_valores`.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`. Como los demas repositorios,
cada funcion recibe el cursor que ya abrio quien llama, ejecuta **una sola
sentencia** y no abre, cierra, confirma ni revierte nada: el `commit` es del
controlador. Ninguna funcion valida; eso lo hace el controlador.

Lo que se vigila es **cuantas** consultas se hacen: contra Neon cada ida y
vuelta cuesta ~180 ms. Por eso ninguna escritura va fila por fila:

- `guardar_calificaciones` escribe todas las subnotas de un estudiante en una
  sentencia, con `UNNEST` y `ON CONFLICT`, como `listas_seguimiento_repository`;
- `borrar_celdas` e `insertar_celdas` rehacen las celdas de todos los
  estudiantes afectados al borrar una subnota en dos sentencias, no dos por
  estudiante.

Esas dos son las unicas escrituras en `notas_detalle` fuera de
`planilla_repository`, y existen solo para ese recalculo en lote. Para la celda
de **un** estudiante el controlador usa las de `planilla_repository`, las
mismas del guardado a mano.

Los tipos de nota se comparan siempre con `LOWER(TRIM(...))`, la misma
expresion de `planilla_repository` y del indice unico de la migracion
`20261021_planilla_subnotas.sql`.
"""


def leer_subnotas_de_planilla(cursor, asignacion_id, periodo):
    """Subnotas de la planilla con sus calificaciones, en orden de creacion.

    Una fila por calificacion, y una con `estudiante_id` vacio por cada subnota
    que nadie ha calificado todavia: `(subnota_id, tipo_nota, nombre,
    estudiante_id, nota, valoracion)`.
    """
    cursor.execute("""
            SELECT s.id, s.tipo_nota, s.nombre, v.estudiante_id, v.nota, v.valoracion
            FROM planilla_subnotas s
            LEFT JOIN planilla_subnotas_valores v ON v.subnota_id = s.id
            WHERE s.asignacion_id = %s AND s.periodo = %s
            ORDER BY s.creada_en, s.id
        """, (asignacion_id, periodo))
    return cursor.fetchall()


def hay_subnotas_calificadas(cursor, asignacion_id, periodo, tipo_nota, estudiante_id):
    """True si el estudiante tiene al menos una subnota calificada en ese tipo.

    Es la comprobacion del `409` de `POST /planilla/nota` (P1).
    """
    cursor.execute("""
            SELECT 1
            FROM planilla_subnotas s
            JOIN planilla_subnotas_valores v ON v.subnota_id = s.id
            WHERE s.asignacion_id = %s AND s.periodo = %s
              AND LOWER(TRIM(s.tipo_nota)) = LOWER(TRIM(%s))
              AND v.estudiante_id = %s
            LIMIT 1
        """, (asignacion_id, periodo, tipo_nota, estudiante_id))
    return cursor.fetchone() is not None


def eliminar_subnotas_del_tipo(cursor, asignacion_id, periodo, tipo_nota):
    """Borra las subnotas de un tipo; sus calificaciones se van en cascada (P6)."""
    cursor.execute("""
            DELETE FROM planilla_subnotas
            WHERE asignacion_id = %s AND periodo = %s
              AND LOWER(TRIM(tipo_nota)) = LOWER(TRIM(%s))
        """, (asignacion_id, periodo, tipo_nota))


def existe_tipo_nota(cursor, asignacion_id, periodo, tipo_nota):
    """True si la planilla tiene ese tipo de nota (alguna fila en notas_detalle)."""
    cursor.execute("""
            SELECT 1
            FROM notas_detalle
            WHERE asignacion_id = %s AND periodo = %s
              AND LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (asignacion_id, periodo, tipo_nota))
    return cursor.fetchone() is not None


def contar_subnotas_del_tipo(cursor, asignacion_id, periodo, tipo_nota, nombre):
    """`(total, con_ese_nombre)` de las subnotas de un tipo, en una consulta.

    Da a la vez el limite de P11 y el nombre repetido, con la misma expresion
    que el indice unico.
    """
    cursor.execute("""
            SELECT
                COUNT(*),
                COUNT(*) FILTER (WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s)))
            FROM planilla_subnotas
            WHERE asignacion_id = %s AND periodo = %s
              AND LOWER(TRIM(tipo_nota)) = LOWER(TRIM(%s))
        """, (nombre, asignacion_id, periodo, tipo_nota))
    total, repetidas = cursor.fetchone()
    return total, repetidas


def insertar_subnota(cursor, asignacion_id, periodo, tipo_nota, nombre):
    """Crea la subnota para todo el curso y devuelve su id."""
    cursor.execute("""
            INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
            VALUES (%s, %s, TRIM(%s), TRIM(%s))
            RETURNING id
        """, (asignacion_id, periodo, tipo_nota, nombre))
    return cursor.fetchone()[0]


def renombrar_subnota(cursor, subnota_id, asignacion_id, nombre):
    """Cambia el nombre. Devuelve False si la subnota no es de esa asignacion.

    El `asignacion_id` va en el `WHERE`: asi nadie renombra la subnota de otra
    clase mandando un id ajeno.
    """
    cursor.execute("""
            UPDATE planilla_subnotas
            SET nombre = TRIM(%s)
            WHERE id = %s AND asignacion_id = %s
            RETURNING id
        """, (nombre, subnota_id, asignacion_id))
    return cursor.fetchone() is not None


def buscar_subnota(cursor, subnota_id, asignacion_id):
    """`(periodo, tipo_nota)` de la subnota, o None si no es de esa asignacion."""
    cursor.execute("""
            SELECT periodo, tipo_nota
            FROM planilla_subnotas
            WHERE id = %s AND asignacion_id = %s
        """, (subnota_id, asignacion_id))
    return cursor.fetchone()


def bloquear_subnotas_del_tipo(cursor, asignacion_id, periodo, tipo_nota):
    """Ids de las subnotas del tipo, bloqueadas hasta el fin de la transaccion.

    El bloqueo hace que dos escrituras sobre el mismo tipo (dos guardados, o un
    guardado y un borrado) vayan una detras de otra. Sin el, cada una podria
    recalcular la celda sin ver lo que escribio la otra.
    """
    cursor.execute("""
            SELECT id
            FROM planilla_subnotas
            WHERE asignacion_id = %s AND periodo = %s
              AND LOWER(TRIM(tipo_nota)) = LOWER(TRIM(%s))
            FOR UPDATE
        """, (asignacion_id, periodo, tipo_nota))
    return [fila[0] for fila in cursor.fetchall()]


def bloquear_subnotas_con_calificaciones_de(
    cursor, asignacion_id, periodo, tipo_nota, estudiante_id
):
    """Las subnotas del tipo, bloqueadas, con lo que ya tiene el estudiante.

    `(subnota_id, nota, valoracion)`, con nota y valoracion vacias donde no
    tiene calificacion. Es el mismo bloqueo de `bloquear_subnotas_del_tipo`, y
    de paso trae lo necesario para recalcular la celda sin otra consulta.
    """
    cursor.execute("""
            SELECT s.id, v.nota, v.valoracion
            FROM planilla_subnotas s
            LEFT JOIN planilla_subnotas_valores v
                ON v.subnota_id = s.id AND v.estudiante_id = %s
            WHERE s.asignacion_id = %s AND s.periodo = %s
              AND LOWER(TRIM(s.tipo_nota)) = LOWER(TRIM(%s))
            ORDER BY s.creada_en, s.id
            FOR UPDATE OF s
        """, (estudiante_id, asignacion_id, periodo, tipo_nota))
    return cursor.fetchall()


def leer_calificaciones_del_tipo(cursor, asignacion_id, periodo, tipo_nota):
    """Todas las calificaciones del tipo: `(subnota_id, estudiante_id, nota, valoracion)`."""
    cursor.execute("""
            SELECT v.subnota_id, v.estudiante_id, v.nota, v.valoracion
            FROM planilla_subnotas_valores v
            JOIN planilla_subnotas s ON s.id = v.subnota_id
            WHERE s.asignacion_id = %s AND s.periodo = %s
              AND LOWER(TRIM(s.tipo_nota)) = LOWER(TRIM(%s))
        """, (asignacion_id, periodo, tipo_nota))
    return cursor.fetchall()


def borrar_subnota(cursor, subnota_id):
    """Borra la subnota; sus calificaciones se van en cascada (P5)."""
    cursor.execute("""
            DELETE FROM planilla_subnotas
            WHERE id = %s
        """, (subnota_id,))


def borrar_calificaciones(cursor, estudiante_id, subnota_ids):
    """Vacia esas subnotas del estudiante. No consulta nada con la lista vacia."""
    if not subnota_ids:
        return
    cursor.execute("""
            DELETE FROM planilla_subnotas_valores
            WHERE estudiante_id = %s AND subnota_id = ANY(%s)
        """, (estudiante_id, list(subnota_ids)))


def guardar_calificaciones(cursor, estudiante_id, calificaciones):
    """Escribe las calificaciones del estudiante en una sola sentencia.

    `calificaciones` es una lista de `(subnota_id, nota, valoracion)` sin ids
    repetidos: `ON CONFLICT DO UPDATE` aborta si la misma fila llega dos veces.
    No consulta nada con la lista vacia.
    """
    if not calificaciones:
        return
    subnota_ids = [subnota_id for subnota_id, _, _ in calificaciones]
    notas = [nota for _, nota, _ in calificaciones]
    valoraciones = [valoracion for _, _, valoracion in calificaciones]
    cursor.execute("""
            INSERT INTO planilla_subnotas_valores (subnota_id, estudiante_id, nota, valoracion)
            SELECT t.subnota_id, %s, t.nota, t.valoracion
            FROM UNNEST(%s::integer[], %s::numeric[], %s::varchar[])
                AS t(subnota_id, nota, valoracion)
            ON CONFLICT (subnota_id, estudiante_id) DO UPDATE
            SET nota = EXCLUDED.nota,
                valoracion = EXCLUDED.valoracion,
                actualizada_en = CURRENT_TIMESTAMP
        """, (estudiante_id, subnota_ids, notas, valoraciones))


def borrar_celdas(cursor, asignacion_id, periodo, tipo_nota, estudiante_ids):
    """Borra las celdas de esos estudiantes en ese tipo, para reinsertarlas.

    Es el mismo par borrar e insertar de `planilla_repository`, en lote.
    """
    cursor.execute("""
            DELETE FROM notas_detalle
            WHERE asignacion_id = %s AND periodo = %s
              AND LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))
              AND estudiante_id = ANY(%s)
        """, (asignacion_id, periodo, tipo_nota, list(estudiante_ids)))


def insertar_celdas(cursor, asignacion_id, periodo, tipo_nota, celdas):
    """Inserta las celdas recalculadas en una sola sentencia.

    `celdas` es una lista de `(estudiante_id, nota, tipo_evaluacion,
    valoracion)`. Las columnas son las mismas de `planilla_repository.insertar_nota`.
    """
    estudiante_ids = [estudiante_id for estudiante_id, _, _, _ in celdas]
    notas = [nota for _, nota, _, _ in celdas]
    tipos = [tipo for _, _, tipo, _ in celdas]
    valoraciones = [valoracion for _, _, _, valoracion in celdas]
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
            SELECT t.estudiante_id, %s, %s, t.nota, TRIM(%s), t.tipo_evaluacion, t.valoracion
            FROM UNNEST(%s::integer[], %s::numeric[], %s::varchar[], %s::varchar[])
                AS t(estudiante_id, nota, tipo_evaluacion, valoracion)
        """, (
        asignacion_id,
        periodo,
        tipo_nota,
        estudiante_ids,
        notas,
        tipos,
        valoraciones,
    ))
