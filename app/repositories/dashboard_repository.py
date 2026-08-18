"""Consultas de `dashboard`, extraidas en la subcapa 7.1.

Cada funcion recibe el cursor que ya abrio el controlador y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el cursor, la normalizacion de `dias`, la resolucion de la
asignacion academica, el formateo del payload y el color de cada fila siguen
siendo del controlador, igual que en los cuatro repositorios anteriores.

El dominio es de **solo lectura**: aqui no hay ni una escritura, ni un `commit`,
ni un `rollback`.

Las cadenas SQL se conservan con su texto original, incluida la sangria, para
que lo que recibe PostgreSQL no cambie. Dos de las ocho no son un literal unico:
las de cumpleanos se **componen** de `_cte_rango_cumpleanos()`, el cuerpo,
`_filtro_rango_cumpleanos()` y el `ORDER BY`, asi que los dos fragmentos viajan
con ellas.

Sobre `leer_estudiantes_por_promedio`: su SQL se arma con f-string. El
comparador, el orden y el filtro de asignacion salen de literales de este mismo
modulo y los valores viajan siempre parametrizados, asi que hoy no es
inyectable. Ninguna extraccion futura debe abrir esa construccion a entrada del
cliente.

Sobre las dos precondiciones de permiso del final: **no filtran por `activo`, y
se conservan asi**. Es un hallazgo abierto de 7.0, no un descuido de esta
subcapa, y corregirlo cambiaria quien puede ver que. Por eso viven aqui y no en
`asignaciones_repository`, donde sus vecinas si filtran y alguien podria
"arreglarlas" sin darse cuenta.
"""


def _cte_rango_cumpleanos():
    return """
        WITH parametros AS (
            SELECT
                (NOW() AT TIME ZONE 'America/Bogota')::date AS hoy,
                ((NOW() AT TIME ZONE 'America/Bogota')::date + %s) AS fecha_fin
        ),
        rango AS (
            SELECT
                hoy,
                fecha_fin,
                TO_CHAR(hoy, 'MMDD') AS inicio_mmdd,
                TO_CHAR(fecha_fin, 'MMDD') AS fin_mmdd
            FROM parametros
        )
    """


def _filtro_rango_cumpleanos(alias_estudiante="e"):
    return f"""
        AND (
            (
                r.inicio_mmdd <= r.fin_mmdd
                AND TO_CHAR({alias_estudiante}.fecha_nacimiento, 'MMDD') BETWEEN r.inicio_mmdd AND r.fin_mmdd
            )
            OR (
                r.inicio_mmdd > r.fin_mmdd
                AND (
                    TO_CHAR({alias_estudiante}.fecha_nacimiento, 'MMDD') >= r.inicio_mmdd
                    OR TO_CHAR({alias_estudiante}.fecha_nacimiento, 'MMDD') <= r.fin_mmdd
                )
            )
        )
    """


def leer_cumpleanos_todos(cursor, dias_normalizados):
    """Cumpleanos de todos los estudiantes activos dentro del rango.

    `LEFT JOIN cursos`: **incluye** a los estudiantes sin curso, a diferencia de
    la consulta del profesor.
    """
    cursor.execute(
            _cte_rango_cumpleanos()
            + """
            SELECT
                e.id,
                e.nombre,
                e.apellido,
                c.nombre AS curso,
                e.fecha_nacimiento
            FROM estudiantes e
            LEFT JOIN cursos c ON e.curso_id = c.id
            CROSS JOIN rango r
            WHERE e.fecha_nacimiento IS NOT NULL
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
            """
            + _filtro_rango_cumpleanos()
            + """
            ORDER BY
                CASE WHEN TO_CHAR(e.fecha_nacimiento, 'MMDD') >= r.inicio_mmdd THEN 0 ELSE 1 END,
                TO_CHAR(e.fecha_nacimiento, 'MMDD') ASC,
                c.nombre ASC NULLS LAST,
                e.apellido ASC,
                e.nombre ASC
            """,
            (dias_normalizados,),
    )
    return cursor.fetchall()


def leer_cumpleanos_de_profesor(cursor, dias_normalizados, profesor_id):
    """Cumpleanos de los estudiantes de los cursos activos de ese profesor.

    Los `dias` van **antes** que el profesor porque el CTE del rango se
    concatena primero.
    """
    cursor.execute(
            _cte_rango_cumpleanos()
            + """
            SELECT
                e.id,
                e.nombre,
                e.apellido,
                c.nombre AS curso,
                e.fecha_nacimiento
            FROM estudiantes e
            JOIN cursos c ON e.curso_id = c.id
            CROSS JOIN rango r
            WHERE EXISTS (
                SELECT 1
                FROM asignaciones a
                WHERE a.curso_id = c.id
                  AND a.profesor_id = %s
                  AND a.activo = TRUE
            )
              AND e.fecha_nacimiento IS NOT NULL
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
              AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
            """
            + _filtro_rango_cumpleanos()
            + """
            ORDER BY
                CASE WHEN TO_CHAR(e.fecha_nacimiento, 'MMDD') >= r.inicio_mmdd THEN 0 ELSE 1 END,
                TO_CHAR(e.fecha_nacimiento, 'MMDD') ASC,
                c.nombre ASC,
                e.apellido ASC,
                e.nombre ASC
            """,
            (dias_normalizados, profesor_id),
    )
    return cursor.fetchall()


def leer_inasistencias_por_curso(cursor, profesor_id):
    """Los tres estudiantes con mas ausencias de cada curso del profesor.

    Solo cuenta `estado ILIKE 'ausente'`, y el corte a tres se hace con
    `ROW_NUMBER()` por curso, no en Python.
    """
    cursor.execute("""
            WITH conteos AS (
                SELECT
                    c.id as curso_id,
                    c.nombre as curso,
                    e.id as estudiante_id,
                    e.nombre || ' ' || e.apellido as nombre_estudiante,
                    COUNT(a.id) as total_fallas,
                    ROW_NUMBER() OVER (
                        PARTITION BY c.id
                        ORDER BY COUNT(a.id) DESC, e.apellido ASC, e.nombre ASC
                    ) as posicion_curso
                FROM asistencia a
                JOIN estudiantes e ON a.estudiante_id = e.id
                JOIN asignaciones asi ON a.asignacion_id = asi.id
                JOIN cursos c ON asi.curso_id = c.id
                WHERE asi.profesor_id = %s AND a.estado ILIKE 'ausente'
                GROUP BY c.id, c.nombre, e.id, e.nombre, e.apellido
            )
            SELECT curso_id, curso, estudiante_id, nombre_estudiante, total_fallas, posicion_curso
            FROM conteos
            WHERE posicion_curso <= 3
            ORDER BY curso ASC, posicion_curso ASC, total_fallas DESC
        """, (profesor_id,))

    return cursor.fetchall()


def leer_estudiantes_por_promedio(cursor, profesor_id, curso_id, asignacion_id, altas):
    """Hasta cinco estudiantes por encima o por debajo de 3,0 en ese curso.

    El promedio es **el promedio de los promedios por clase**, que no es la
    misma cifra que el de los rankings. Ver el hallazgo de 7.0.
    """
    filtro_asignacion = "AND asi.id = %s" if asignacion_id is not None else ""
    params = [profesor_id, curso_id]
    if asignacion_id is not None:
        params.append(asignacion_id)

    comparador = ">= 3.0" if altas else "< 3.0"
    orden = "DESC" if altas else "ASC"

    cursor.execute(f"""
            WITH PromediosPorClase AS (
                SELECT
                    e.id as estudiante_id,
                    e.nombre,
                    e.apellido,
                    c.nombre as curso,
                    m.nombre as materia,
                    AVG(CAST(n.nota AS numeric)) as promedio_clase
                FROM notas_detalle n
                JOIN estudiantes e ON n.estudiante_id = e.id
                JOIN asignaciones asi ON n.asignacion_id = asi.id
                JOIN cursos c ON asi.curso_id = c.id
                JOIN materias m ON asi.materia_id = m.id
                WHERE asi.profesor_id = %s
                  AND asi.curso_id = %s
                  AND n.nota IS NOT NULL
                  {filtro_asignacion}
                GROUP BY e.id, e.nombre, e.apellido, c.nombre, m.nombre, asi.id
            )
            SELECT
                nombre || ' ' || apellido as nombre_estudiante,
                MAX(curso) as curso,
                CASE WHEN %s IS NULL THEN 'Todas las materias' ELSE MAX(materia) END as materia,
                TRUNC(AVG(promedio_clase), 2) as promedio
            FROM PromediosPorClase
            GROUP BY estudiante_id, nombre, apellido
            HAVING TRUNC(AVG(promedio_clase), 2) {comparador}
            ORDER BY promedio {orden}, nombre ASC, apellido ASC
            LIMIT 5
        """, (*params, asignacion_id))

    return cursor.fetchall()


def leer_ranking_bajo_rendimiento(cursor, asignacion_id, periodo):
    """Estudiantes por debajo de 3,0 en esa asignacion y periodo, peor primero.

    Aqui el promedio es **plano sobre las notas**, no un promedio de promedios.
    """
    cursor.execute("""
            SELECT
                e.id as estudiante_id,
                e.nombre || ' ' || e.apellido as nombre_estudiante,
                TRUNC(AVG(CAST(n.nota AS numeric)), 2) as promedio
            FROM notas_detalle n
            JOIN estudiantes e ON n.estudiante_id = e.id
            WHERE n.asignacion_id = %s AND n.periodo = %s
            GROUP BY e.id, e.nombre, e.apellido
            HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) < 3.0
            ORDER BY promedio ASC
        """, (asignacion_id, periodo))

    return cursor.fetchall()


def leer_ranking_mejor_rendimiento(cursor, asignacion_id, periodo):
    """Gemela de `leer_ranking_bajo_rendimiento` salvo el signo y el orden.

    Las dos cadenas se conservan separadas: unificarlas es legitimo pero es
    decision del usuario, igual que las tres parejas gemelas de la capa 6.
    """
    cursor.execute("""
            SELECT
                e.id as estudiante_id,
                e.nombre || ' ' || e.apellido as nombre_estudiante,
                TRUNC(AVG(CAST(n.nota AS numeric)), 2) as promedio
            FROM notas_detalle n
            JOIN estudiantes e ON n.estudiante_id = e.id
            WHERE n.asignacion_id = %s AND n.periodo = %s
            GROUP BY e.id, e.nombre, e.apellido
            HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) >= 3.0
            ORDER BY promedio DESC
        """, (asignacion_id, periodo))

    return cursor.fetchall()


def buscar_curso_de_profesor(cursor, profesor_id, curso_id):
    """Fila testigo si ese profesor tiene alguna asignacion en ese curso.

    **No filtra por `activo`**: una asignacion desactivada sigue dando acceso.
    Es el primer hallazgo de 7.0 y se conserva tal cual.
    """
    cursor.execute(
            """
            SELECT 1
            FROM asignaciones
            WHERE profesor_id = %s AND curso_id = %s
            LIMIT 1
            """,
            (profesor_id, curso_id),
    )
    return cursor.fetchone()


def buscar_asignacion_de_profesor_en_curso(cursor, asignacion_id, profesor_id, curso_id):
    """Fila testigo si esa asignacion es de ese profesor y ese curso.

    Recibe el id **ya resuelto** a asignacion academica: quien resuelve es el
    controlador. **Tampoco filtra por `activo`.**
    """
    cursor.execute(
            """
            SELECT 1
            FROM asignaciones
            WHERE id = %s AND profesor_id = %s AND curso_id = %s
            LIMIT 1
            """,
            (asignacion_id, profesor_id, curso_id),
    )
    return cursor.fetchone()
