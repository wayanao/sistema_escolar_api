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
"""


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

def leer_materias_del_estudiante(cursor, estudiante_id, periodo, nombre_materia_excluida):
    """Materias del curso con su definitiva.

    `COALESCE(NULLIF(bc.definitiva, 0), ...)` trata una definitiva guardada como
    **0** como si fuera ausente y la sustituye por el promedio calculado: es el
    hallazgo 4 de 7.0 y se conserva. El promedio se calcula **en SQL**, con
    `AVG`, a diferencia del reporte parcial.

    `nombre_materia_excluida` deja fuera la asignacion de jornada de
    preescolar (nivel academico): esa asignacion existe para tomar
    asistencia una vez al dia, no es una materia real y no debe aparecer en
    el boletin. Ver app.core.nivel_academico.NOMBRE_MATERIA_ASISTENCIA_JORNADA.
    """
    cursor.execute('''
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
            JOIN asignaciones_academicas asig ON e.curso_id = asig.curso_id
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
            ORDER BY asig.orden_boletin, m.nombre
        ''', (periodo, periodo, estudiante_id, nombre_materia_excluida))
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


def leer_datos_del_estudiante(cursor, estudiante_id):
    """Nombre, apellido, curso, jornada y director de grupo del curso. Devuelve
    `None` si el estudiante no existe, y eso es lo que acaba siendo el **404**
    de la ruta."""
    cursor.execute('''
            SELECT e.nombre as estudiante_nombre, e.apellido as estudiante_apellido,
                   c.nombre as curso_nombre, c.jornada as jornada,
                   dg.nombre as director_grupo_nombre, dg.apellido as director_grupo_apellido
            FROM estudiantes e
            LEFT JOIN cursos c ON e.curso_id = c.id
            LEFT JOIN profesor dg ON dg.id = c.director_grupo_id
            WHERE e.id = %s
        ''', (estudiante_id,))
    return cursor.fetchone()


def leer_puesto_en_el_curso(cursor, estudiante_id, periodo):
    """Puesto del estudiante en su curso y total de rankeados.

    Promedia las definitivas no nulas por estudiante y rankea descendente. Solo
    entran las numericas, porque una definitiva `NULL` queda fuera del `AVG`.
    """
    cursor.execute('''
            WITH promedios AS (
                SELECT
                    bc.estudiante_id,
                    AVG(bc.definitiva) AS promedio
                FROM boletin_cabecera bc
                JOIN estudiantes e ON e.id = bc.estudiante_id
                WHERE e.curso_id = (SELECT curso_id FROM estudiantes WHERE id = %s)
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
        ''', (estudiante_id, periodo, estudiante_id))
    return cursor.fetchone()


# --------------------------------------------------------------------------
# Lectura: reporte parcial
# --------------------------------------------------------------------------

def leer_datos_basicos_del_estudiante(cursor, estudiante_id):
    """Mismo resultado que `leer_datos_del_estudiante` con **otro SQL**.

    Cambian el orden del `LEFT JOIN` y el formato de las columnas. Se conservan
    las dos por separado: unificarlas cambiaria el SQL observable de uno de los
    dos caminos y esta capa no lo autoriza.
    """
    cursor.execute('''
            SELECT
                e.nombre AS estudiante_nombre,
                e.apellido AS estudiante_apellido,
                c.nombre AS curso_nombre,
                c.jornada AS jornada,
                dg.nombre AS director_grupo_nombre,
                dg.apellido AS director_grupo_apellido
            FROM estudiantes e
            LEFT JOIN cursos c ON c.id = e.curso_id
            LEFT JOIN profesor dg ON dg.id = c.director_grupo_id
            WHERE e.id = %s
        ''', (estudiante_id,))
    return cursor.fetchone()


def leer_planilla_vigente(cursor, estudiante_id, periodo, nombre_materia_excluida):
    """Planilla vigente del estudiante: materias y notas sin pasar por el
    boletin guardado. Es la fotografia que sostiene el reporte parcial.

    `nombre_materia_excluida`: ver el mismo parametro en
    `leer_materias_del_estudiante`.
    """
    cursor.execute('''
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
            JOIN asignaciones_academicas asig ON asig.curso_id = e.curso_id
            JOIN materias m ON m.id = asig.materia_id
            JOIN profesor p ON p.id = asig.profesor_id
            LEFT JOIN notas_detalle nd
                ON nd.estudiante_id = e.id
                AND nd.asignacion_id = asig.id
                AND nd.periodo = %s
            WHERE e.id = %s
              AND m.nombre <> %s
            ORDER BY asig.orden_boletin, m.nombre, nd.id
        ''', (periodo, estudiante_id, nombre_materia_excluida))
    return cursor.fetchall()
