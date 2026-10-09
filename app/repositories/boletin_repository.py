"""Consultas y escritura de `boletin`, extraidas en la subcapa 7.1.

Cada funcion recibe el cursor que ya abrio quien la llama y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el `commit`, el `rollback`, la resolucion de la asignacion
academica, los promedios y el armado del payload siguen fuera de aqui, igual que
en los nueve repositorios anteriores. Este es el **decimo**.

Este dominio **escribe dos tablas** —`boletin_cabecera` y `boletin_detalles`—,
la primera vez que ocurre en la capa 7. Lo hace con un reemplazo parcial
transaccional: `guardar_cabecera` hace un `UPSERT`, `borrar_detalles_de_boletin`
vacia el detalle y se llama a `insertar_detalle` una vez por detalle, todo
dentro de la unica transaccion propia del dominio. El `commit` **no** es de
este modulo.

Las cadenas SQL se conservan con su texto original tras la limpieza de espacios
finales que 7.1 autorizo de forma explicita. Esa limpieza se hizo **antes** de
mover nada y se demostro inocua: los doce literales resultan identicos al
comparar linea a linea sin espacios finales, y ninguna sentencia cambio de
palabras, orden ni parametros.

Lo que **no** vive aqui, y es deliberado:

- **`obtener_notas_planilla_controller` conserva su SQL inline.** Es codigo
  muerto que pertenece a `planilla`, no a este dominio, y no tiene un solo
  consumidor. Traerlo aqui habria creado una funcion que nadie llama y una
  falsa declaracion de propiedad sobre un dominio en espera. Es el hallazgo 5
  de 7.0 y se conserva tal cual.
- **Las dos lecturas de los datos del estudiante siguen separadas.**
  `leer_datos_del_estudiante` y `leer_datos_basicos_del_estudiante` devuelven lo
  mismo con SQL distinto —cambia el orden del `LEFT JOIN` y el de las columnas—.
  Unificarlas cambiaria el SQL observable de uno de los dos caminos y no esta
  autorizado: la regla del programa es no crear una abstraccion compartida sin
  dos usos reales, y aqui los usos existen pero los textos difieren.
- **El emparejamiento por posicion de las observaciones guardadas** sigue en el
  controlador. Es el hallazgo 1 de 7.0, el mas grave del dominio, y 7.1 **no lo
  corrige**: moverlo o arreglarlo cambiaria comportamiento.

Año lectivo, fase 3 (paso 3.5a, ver `docs/funcionalidades/ANIO_LECTIVO.md`):
las lecturas del boletin de administracion y del reporte parcial aceptan
`anio_lectivo_id`, un año que **no** es el activo. Sin el, el curso del
estudiante sigue siendo `e.curso_id` y el texto que recibe PostgreSQL es el de
siempre; con el, el curso es el de su matricula de ese año. La excepcion es el
puesto, que cambia tambien sin año: ver `leer_puesto_en_el_curso`.

Fase 6 (paso 6.3b): con año, las dos consultas de materias de un año cerrado
o reabierto ocultan las de su foto al cerrarse, no las inactivas de hoy. Ver
`_materia_visible`.
"""

from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL


def _curso_del_estudiante(anio_lectivo_id):
    """El curso del estudiante `e` dentro de una consulta, y sus parametros.

    Sin año, `e.curso_id`: el curso del año activo, con el texto de siempre.
    Con año, el de su matricula de ese año, o `NULL` si no estuvo matriculado.
    """
    if anio_lectivo_id is None:
        return "e.curso_id", ()
    return (
        "(SELECT m.curso_id FROM matriculas m"
        " WHERE m.estudiante_id = e.id AND m.anio_lectivo_id = %s)",
        (anio_lectivo_id,),
    )


_MATERIA_ACTIVA = "COALESCE(LOWER(m.estado), 'activo') = 'activo'"


def _materia_visible(anio_lectivo_id):
    """Qué materias `m` salen en el boletín, y sus parametros.

    Sin año, las activas: el texto de siempre. Con año, si ese año está
    cerrado o reabierto, todas menos las de su foto al cerrarse (año lectivo,
    decisión 13 y paso 6.3b); si no, las activas, igual que sin año.
    """
    if anio_lectivo_id is None:
        return _MATERIA_ACTIVA, ()
    return (
        f"""CASE WHEN (SELECT estado FROM anios_lectivos WHERE id = %s)
                     IN ('cerrado', 'reabierto')
                THEN NOT EXISTS (
                    SELECT 1 FROM anios_lectivos_materias_ocultas o
                    WHERE o.anio_lectivo_id = %s AND o.materia_id = m.id
                )
                ELSE {_MATERIA_ACTIVA}
              END""",
        (anio_lectivo_id, anio_lectivo_id),
    )


# --------------------------------------------------------------------------
# Escritura: reemplazo parcial transaccional
# --------------------------------------------------------------------------

def guardar_cabecera(cursor, estudiante_id, asignacion_id, periodo, definitiva):
    """`UPSERT` de la cabecera y devuelve su id.

    **No filtra `activo`** en la asignacion resuelta: es el hallazgo 8 de 7.0 y
    se conserva.
    """
    cursor.execute("""
            INSERT INTO boletin_cabecera (estudiante_id, asignacion_id, periodo, definitiva)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (estudiante_id, asignacion_id, periodo)
            DO UPDATE SET definitiva = EXCLUDED.definitiva
            RETURNING id
        """, (estudiante_id, asignacion_id, periodo, definitiva))
    return cursor.fetchone()[0]


def borrar_detalles_de_boletin(cursor, boletin_id):
    """Vacia el detalle del boletin.

    Se ejecuta **siempre**, aunque el lote entrante venga vacio: es el hallazgo
    6 de 7.0 y se conserva.
    """
    cursor.execute("DELETE FROM boletin_detalles WHERE boletin_id = %s", (boletin_id,))


def insertar_detalle(cursor, boletin_id, nota, observacion, tipo_evaluacion, valoracion):
    """Un detalle del boletin. Se llama una vez por elemento del lote."""
    cursor.execute("""
                INSERT INTO boletin_detalles (
                    boletin_id,
                    nota,
                    observacion,
                    tipo_evaluacion,
                    valoracion
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
        boletin_id,
        nota,
        observacion,
        tipo_evaluacion,
        valoracion,
    ))


# --------------------------------------------------------------------------
# Lectura: referencia del profesor
# --------------------------------------------------------------------------

def leer_notas_de_planilla(cursor, asignacion_id, periodo):
    """Notas vigentes de la planilla de una asignacion, con sus valoraciones."""
    cursor.execute("""
            SELECT e.id as estudiante_id, e.nombre, e.apellido,
                   nd.descripcion as tipo_nota,
                   nd.nota,
                   COALESCE(nd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                   nd.valoracion
            FROM estudiantes e
            JOIN asignaciones a ON e.curso_id = a.curso_id
            LEFT JOIN notas_detalle nd ON e.id = nd.estudiante_id
                AND nd.asignacion_id = a.id AND nd.periodo = %s
            WHERE a.id = %s
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
            ORDER BY e.apellido, e.nombre, nd.id
        """, (periodo, asignacion_id))
    return cursor.fetchall()


def leer_boletines_guardados_de_estudiantes(cursor, asignacion_id, periodo, estudiante_ids):
    """Lo ya guardado en el boletin para un lote de estudiantes.

    Pide el lote entero con `= ANY(%s)`: **no hay N+1**, y esa es la linea base
    que 7.0 dejo fijada por asercion.
    """
    cursor.execute("""
                SELECT
                    bc.estudiante_id,
                    bc.definitiva,
                    bd.nota,
                    bd.observacion,
                    COALESCE(bd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                    bd.valoracion
                FROM boletin_cabecera bc
                JOIN boletin_detalles bd ON bd.boletin_id = bc.id
                WHERE bc.asignacion_id = %s AND bc.periodo = %s
                    AND bc.estudiante_id = ANY(%s)
                ORDER BY bc.estudiante_id, bd.id
            """, (asignacion_id, periodo, estudiante_ids))
    return cursor.fetchall()


# --------------------------------------------------------------------------
# Lectura: boletin de administracion
# --------------------------------------------------------------------------

def leer_materias_del_estudiante(
    cursor, estudiante_id, periodo, nombre_materia_excluida, anio_lectivo_id=None
):
    """Materias del curso con su definitiva.

    `COALESCE(NULLIF(bc.definitiva, 0), ...)` trata una definitiva guardada como
    **0** como si fuera ausente y la sustituye por el promedio calculado: es el
    hallazgo 4 de 7.0 y se conserva. El promedio se calcula **en SQL**, con
    `AVG`, a diferencia del reporte parcial.

    `nombre_materia_excluida` deja fuera la asignacion de jornada de
    preescolar (nivel academico): esa asignacion existe para tomar
    asistencia una vez al dia, no es una materia real y no debe aparecer en
    el boletin. Ver app.core.nivel_academico.NOMBRE_MATERIA_ASISTENCIA_JORNADA.

    Una materia inactiva no sale, **tampoco en los periodos ya calificados**.
    Es la misma regla que ya aplicaba `a.activo` para la asignacion, y la que
    usan las ocho consultas de `asignaciones_repository`. El filtro faltaba
    aqui desde que se anadio `materias.estado` (20260604_materias_estado.sql):
    la asignatura desaparecia de todas las pantallas menos del boletin.

    Con `anio_lectivo_id`, las materias del curso de su matricula de ese año.
    Si ese año está cerrado, las que oculta su foto: ver `_materia_visible`.
    """
    curso, params_curso = _curso_del_estudiante(anio_lectivo_id)
    materia_visible, params_materia = _materia_visible(anio_lectivo_id)
    cursor.execute(f'''
            WITH asignaciones_academicas AS (
                SELECT DISTINCT ON (COALESCE(a.asignacion_academica_id, a.id))
                    COALESCE(a.asignacion_academica_id, a.id) AS id,
                    a.curso_id,
                    a.materia_id,
                    a.profesor_id,
                    COALESCE(a.orden_boletin, 100) AS orden_boletin
                FROM asignaciones a
                WHERE a.activo = TRUE
                ORDER BY COALESCE(a.asignacion_academica_id, a.id), COALESCE(a.orden_boletin, 100), a.id
            )
            SELECT
                asig.id as asignacion_id,
                m.id as materia_id,
                m.nombre AS materia,
                p.nombre AS profesor_nombre,
                p.apellido AS profesor_apellido,
                COALESCE(NULLIF(bc.definitiva, 0), nd_prom.promedio_numerico) AS definitiva,
                bc.id as boletin_id,
                asig.orden_boletin
            FROM estudiantes e
            JOIN asignaciones_academicas asig ON {curso} = asig.curso_id
            JOIN materias m ON asig.materia_id = m.id
            JOIN profesor p ON asig.profesor_id = p.id
            LEFT JOIN boletin_cabecera bc ON bc.asignacion_id = asig.id
                AND bc.estudiante_id = e.id
                AND bc.periodo = %s
            LEFT JOIN LATERAL (
                SELECT AVG(nd.nota) AS promedio_numerico
                FROM notas_detalle nd
                WHERE nd.estudiante_id = e.id
                  AND nd.asignacion_id = asig.id
                  AND nd.periodo = %s
                  AND COALESCE(nd.tipo_evaluacion, 'numerica') <> 'desarrollo'
                  AND nd.nota > 0
            ) nd_prom ON TRUE
            WHERE e.id = %s
              AND m.nombre <> %s
              AND {materia_visible}
            ORDER BY asig.orden_boletin, m.nombre
        ''', (
            *params_curso, periodo, periodo, estudiante_id, nombre_materia_excluida,
            *params_materia,
        ))
    return cursor.fetchall()


def leer_detalles_por_asignaciones(cursor, periodo, estudiante_id, asignacion_ids):
    """Detalles guardados de todos los periodos, en lote y numerados.

    La observacion solo se devuelve para el periodo pedido; los demas periodos
    llegan con `NULL` para que el historico no arrastre textos ajenos.
    """
    cursor.execute('''
                SELECT
                    bc.asignacion_id,
                    bc.periodo,
                    bd.nota,
                    COALESCE(bd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                    bd.valoracion,
                    CASE WHEN bc.periodo = %s THEN bd.observacion ELSE NULL END AS observacion,
                    ROW_NUMBER() OVER (
                        PARTITION BY bc.asignacion_id, bc.periodo
                        ORDER BY bd.id
                    ) AS detalle_idx
                FROM boletin_cabecera bc
                JOIN boletin_detalles bd ON bd.boletin_id = bc.id
                WHERE bc.estudiante_id = %s
                    AND bc.asignacion_id = ANY(%s)
                    AND bc.periodo BETWEEN 1 AND 4
                ORDER BY bc.asignacion_id, detalle_idx, bc.periodo
            ''', (periodo, estudiante_id, asignacion_ids))
    return cursor.fetchall()


def leer_datos_del_estudiante(cursor, estudiante_id, anio_lectivo_id=None):
    """Nombre, apellido, curso, jornada y director de grupo del curso. Devuelve
    `None` si el estudiante no existe, y eso es lo que acaba siendo el **404**
    de la ruta. Con `anio_lectivo_id`, el curso de su matricula de ese año."""
    curso, params_curso = _curso_del_estudiante(anio_lectivo_id)
    cursor.execute(f'''
            SELECT e.nombre as estudiante_nombre, e.apellido as estudiante_apellido,
                   c.nombre as curso_nombre, c.jornada as jornada,
                   dg.nombre as director_grupo_nombre, dg.apellido as director_grupo_apellido
            FROM estudiantes e
            LEFT JOIN cursos c ON {curso} = c.id
            LEFT JOIN profesor dg ON dg.id = c.director_grupo_id
            WHERE e.id = %s
        ''', (*params_curso, estudiante_id))
    return cursor.fetchone()


def leer_puesto_en_el_curso(cursor, estudiante_id, periodo, anio_lectivo_id=None):
    """Puesto del estudiante en su curso y total de rankeados.

    Promedia las definitivas no nulas por estudiante y rankea descendente. Solo
    entran las numericas, porque una definitiva `NULL` queda fuera del `AVG`.

    Año lectivo (fase 3, paso 3.5a): solo cuentan las definitivas de cursos
    del año que se mira, **tambien sin año**. El periodo 1 existe en todos los
    años; sin este filtro, con 2027 activo, el puesto del periodo 1 promediaria
    tambien las definitivas del periodo 1 de 2026 de quien estuvo los dos años.
    Mientras haya un solo año, el resultado es el mismo de antes. Con
    `anio_lectivo_id`, los compañeros son los matriculados en el mismo curso
    ese año.
    """
    curso, params_curso = _curso_del_estudiante(anio_lectivo_id)
    if anio_lectivo_id is None:
        curso_del_pedido = "(SELECT curso_id FROM estudiantes WHERE id = %s)"
        params_pedido = (estudiante_id,)
        anio_sql, params_anio = ANIO_ACTIVO_ID_SQL, ()
    else:
        curso_del_pedido = (
            "(SELECT curso_id FROM matriculas WHERE estudiante_id = %s AND anio_lectivo_id = %s)"
        )
        params_pedido = (estudiante_id, anio_lectivo_id)
        anio_sql, params_anio = "%s", (anio_lectivo_id,)
    cursor.execute(f'''
            WITH promedios AS (
                SELECT
                    bc.estudiante_id,
                    AVG(bc.definitiva) AS promedio
                FROM boletin_cabecera bc
                JOIN estudiantes e ON e.id = bc.estudiante_id
                JOIN asignaciones a ON a.id = bc.asignacion_id
                JOIN cursos c ON c.id = a.curso_id
                WHERE {curso} = {curso_del_pedido}
                  AND c.anio_lectivo_id = {anio_sql}
                  AND bc.periodo = %s
                  AND bc.definitiva IS NOT NULL
                GROUP BY bc.estudiante_id
            ),
            ranked AS (
                SELECT
                    estudiante_id,
                    promedio,
                    RANK() OVER (ORDER BY promedio DESC) AS puesto
                FROM promedios
            )
            SELECT
                (SELECT puesto FROM ranked WHERE estudiante_id = %s) AS puesto,
                (SELECT COUNT(*) FROM promedios) AS total
        ''', (*params_curso, *params_pedido, *params_anio, periodo, estudiante_id))
    return cursor.fetchone()


# --------------------------------------------------------------------------
# Lectura: reporte parcial
# --------------------------------------------------------------------------

def leer_datos_basicos_del_estudiante(cursor, estudiante_id, anio_lectivo_id=None):
    """Mismo resultado que `leer_datos_del_estudiante` con **otro SQL**.

    Cambian el orden del `LEFT JOIN` y el formato de las columnas. Se conservan
    las dos por separado: unificarlas cambiaria el SQL observable de uno de los
    dos caminos y esta capa no lo autoriza.

    Con `anio_lectivo_id`, el curso de su matricula de ese año.
    """
    curso, params_curso = _curso_del_estudiante(anio_lectivo_id)
    cursor.execute(f'''
            SELECT
                e.nombre AS estudiante_nombre,
                e.apellido AS estudiante_apellido,
                c.nombre AS curso_nombre,
                c.jornada AS jornada,
                dg.nombre AS director_grupo_nombre,
                dg.apellido AS director_grupo_apellido
            FROM estudiantes e
            LEFT JOIN cursos c ON c.id = {curso}
            LEFT JOIN profesor dg ON dg.id = c.director_grupo_id
            WHERE e.id = %s
        ''', (*params_curso, estudiante_id))
    return cursor.fetchone()


def leer_planilla_vigente(
    cursor, estudiante_id, periodo, nombre_materia_excluida, anio_lectivo_id=None
):
    """Planilla vigente del estudiante: materias y notas sin pasar por el
    boletin guardado. Es la fotografia que sostiene el reporte parcial.

    `nombre_materia_excluida`: ver el mismo parametro en
    `leer_materias_del_estudiante`. El filtro de materia inactiva tambien se
    explica alli: las dos consultas del boletin siguen la misma regla.

    Con `anio_lectivo_id`, las materias del curso de su matricula de ese año.
    Si ese año está cerrado, las que oculta su foto: ver `_materia_visible`.
    """
    curso, params_curso = _curso_del_estudiante(anio_lectivo_id)
    materia_visible, params_materia = _materia_visible(anio_lectivo_id)
    cursor.execute(f'''
            WITH asignaciones_academicas AS (
                SELECT DISTINCT ON (COALESCE(a.asignacion_academica_id, a.id))
                    COALESCE(a.asignacion_academica_id, a.id) AS id,
                    a.curso_id,
                    a.materia_id,
                    a.profesor_id,
                    COALESCE(a.orden_boletin, 100) AS orden_boletin
                FROM asignaciones a
                WHERE a.activo = TRUE
                ORDER BY
                    COALESCE(a.asignacion_academica_id, a.id),
                    COALESCE(a.orden_boletin, 100),
                    a.id
            )
            SELECT
                asig.id AS asignacion_id,
                m.id AS materia_id,
                m.nombre AS materia,
                p.nombre AS profesor_nombre,
                p.apellido AS profesor_apellido,
                asig.orden_boletin,
                nd.id AS nota_detalle_id,
                nd.descripcion,
                nd.nota,
                COALESCE(nd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                nd.valoracion
            FROM estudiantes e
            JOIN asignaciones_academicas asig ON asig.curso_id = {curso}
            JOIN materias m ON m.id = asig.materia_id
            JOIN profesor p ON p.id = asig.profesor_id
            LEFT JOIN notas_detalle nd
                ON nd.estudiante_id = e.id
                AND nd.asignacion_id = asig.id
                AND nd.periodo = %s
            WHERE e.id = %s
              AND m.nombre <> %s
              AND {materia_visible}
            ORDER BY asig.orden_boletin, m.nombre, nd.id
        ''', (*params_curso, periodo, estudiante_id, nombre_materia_excluida, *params_materia))
    return cursor.fetchall()
