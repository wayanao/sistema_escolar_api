"""Consultas y escritura de `notas`, extraidas en la subcapa 7.1.

Cada funcion recibe el cursor que ya abrio quien la llama y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el `commit`, la resolucion de la asignacion academica, el calculo
de promedios, el formateo del payload y las actividades sinteticas del boletin
detallado siguen fuera de aqui, igual que en los seis repositorios anteriores.

A diferencia de `dashboard`, este dominio **escribe**: `insertar_nota` es la
unica escritura, sobre la unica tabla escrita y dentro de la unica transaccion
propia del dominio. El `commit` **no** es de este modulo.

Quien abre el cursor no siempre es un controlador. Las tres funciones de
validacion las llama `app/services/nota_service.py`, que **conserva la
propiedad de su conexion**: cada una abre la suya, igual que antes de esta
subcapa. Unificarlas en un solo cursor cambiaria el numero de conexiones que
7.0 dejo medido, y no esta autorizado aqui.

Las cadenas SQL se conservan con su texto original, incluida la sangria, para
que lo que recibe PostgreSQL no cambie.

Sobre `buscar_asignacion`: **no filtra por `activo`, y se conserva asi**. Es un
hallazgo abierto de 7.0 y corregirlo cambiaria quien puede escribir notas. Vive
aqui y no en `asignaciones_repository`, donde sus vecinas si filtran y alguien
podria "arreglarla" por vecindad. El mismo criterio que 7.1 de dashboard aplico
a sus dos precondiciones de permiso.

Sobre `periodo`: `insertar_nota` **no fija esa columna** y solo
`leer_notas_de_asignacion_en_periodo` filtra por ella. Es otro hallazgo abierto
de 7.0; aqui se conserva exactamente como estaba.
"""


def insertar_nota(cursor, estudiante_id, asignacion_id, nota, descripcion):
    """Inserta la nota y devuelve su id.

    No fija `periodo`: la columna toma el valor por defecto de la base.
    Es un hallazgo abierto de 7.0 y se conserva.
    """
    cursor.execute("""
            INSERT INTO notas_detalle (
                estudiante_id,
                asignacion_id,
                nota,
                descripcion
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (estudiante_id, asignacion_id, nota, descripcion))
    return cursor.fetchone()[0]


def leer_notas_de_estudiante(cursor, estudiante_id):
    """Notas y descripciones de un estudiante, sin filtrar por periodo."""
    cursor.execute("""
            SELECT
                nd.nota,
                nd.descripcion
            FROM notas_detalle nd
            WHERE nd.estudiante_id = %s
        """, (estudiante_id,))
    return cursor.fetchall()


def leer_boletin_de_estudiante(cursor, estudiante_id):
    """Promedio por materia del boletin, agregando todos los periodos."""
    cursor.execute("""
            WITH asignaciones_academicas AS (
                SELECT DISTINCT ON (COALESCE(a.asignacion_academica_id, a.id))
                    COALESCE(a.asignacion_academica_id, a.id) AS id,
                    a.curso_id,
                    a.materia_id,
                    COALESCE(a.orden_boletin, 100) AS orden_boletin
                FROM asignaciones a
                WHERE a.activo = TRUE
                ORDER BY COALESCE(a.asignacion_academica_id, a.id), COALESCE(a.orden_boletin, 100), a.id
            )
            SELECT
                e.nombre,
                e.apellido,
                c.nombre AS curso,
                m.nombre AS materia,
                COALESCE(AVG(nd.nota), 0) AS promedio_materia

            FROM estudiantes e
            JOIN cursos c ON e.curso_id = c.id
            JOIN asignaciones_academicas a ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id

            LEFT JOIN notas_detalle nd
                ON nd.estudiante_id = e.id
                AND nd.asignacion_id = a.id

            WHERE e.id = %s

            GROUP BY e.nombre, e.apellido, c.nombre, m.nombre, a.orden_boletin
            ORDER BY a.orden_boletin, m.nombre
        """, (estudiante_id,))
    return cursor.fetchall()


def leer_planilla_de_asignacion(cursor, asignacion_id):
    """Promedio por estudiante activo de una asignacion.

    Recibe el id **ya resuelto** a asignacion academica: quien resuelve es el
    controlador.
    """
    cursor.execute("""
            SELECT
                e.id,
                e.nombre,
                e.apellido,
                m.nombre AS materia,
                c.nombre AS curso,
                COALESCE(AVG(nd.nota), 0) AS promedio

            FROM asignaciones a

            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            JOIN estudiantes e ON e.curso_id = c.id

            LEFT JOIN notas_detalle nd
                ON nd.estudiante_id = e.id
                AND nd.asignacion_id = a.id

            WHERE a.id = %s
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'

            GROUP BY e.id, e.nombre, e.apellido, m.nombre, c.nombre
            ORDER BY e.nombre
        """, (asignacion_id,))
    return cursor.fetchall()


def leer_asignaciones_del_estudiante(cursor, estudiante_id):
    """Materias, docente y asignacion academica del curso del estudiante."""
    cursor.execute("""
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
                m.id,
                m.nombre AS area,
                p.nombre || ' ' || p.apellido AS docente,
                a.id AS asignacion_id
            FROM estudiantes e
            JOIN cursos c ON e.curso_id = c.id
            JOIN asignaciones_academicas a ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            JOIN profesor p ON a.profesor_id = p.id
            WHERE e.id = %s
            ORDER BY a.orden_boletin, m.nombre
        """, (estudiante_id,))
    return cursor.fetchall()


def leer_notas_de_asignacion_en_periodo(cursor, estudiante_id, asignacion_id, periodo):
    """Notas guardadas de una asignacion en un periodo.

    Es la unica lectura del dominio que filtra por `periodo`. Se llama una vez
    por asignacion dentro de un bucle: el N+1 del boletin detallado es un
    hallazgo abierto de 7.0 y **no se corrige aqui**.
    """
    cursor.execute("""
                SELECT id, descripcion, nota
                FROM notas_detalle
                WHERE estudiante_id = %s AND asignacion_id = %s AND periodo = %s
                ORDER BY id ASC
            """, (estudiante_id, asignacion_id, periodo))
    return cursor.fetchall()


def buscar_asignacion(cursor, asignacion_id):
    """Fila testigo de que la asignacion existe.

    **No filtra por `activo`**: una asignacion desactivada sigue permitiendo
    registrar notas. Es un hallazgo abierto de 7.0 y se conserva tal cual.
    """
    cursor.execute("""
            SELECT id FROM asignaciones
            WHERE id = %s
        """, (asignacion_id,))
    return cursor.fetchone()


def buscar_estudiante(cursor, estudiante_id):
    """Fila testigo de que el estudiante existe."""
    cursor.execute("""
            SELECT id FROM estudiantes
            WHERE id = %s
        """, (estudiante_id,))
    return cursor.fetchone()


def buscar_estudiante_en_curso_de_asignacion(cursor, estudiante_id, asignacion_id):
    """Fila testigo de que el estudiante pertenece al curso de la asignacion."""
    cursor.execute("""
            SELECT e.id
            FROM estudiantes e
            JOIN asignaciones a ON e.curso_id = a.curso_id
            WHERE e.id = %s AND a.id = %s
        """, (estudiante_id, asignacion_id))
    return cursor.fetchone()
