"""Lecturas de "Mi curso" del director de grupo.

Ver `docs/funcionalidades/MI_CURSO_DIRECTOR.md`. Todas son del **año
lectivo activo**, como el resto del perfil profesor. Solo escriben las dos de
la observacion general (paso 3), al final del archivo; el `commit` es de quien
llama.

Cada funcion recibe el cursor de quien llama y ejecuta una sola sentencia, como
en los demas repositorios: abrir, cerrar y confirmar no es de este modulo.

El curso entero sale en un numero fijo de consultas (curso, materias,
estudiantes con su puesto, definitivas e inasistencias), sin una por
estudiante ni una por materia.

Las reglas del boletin se copian a proposito y no se reinterpretan, para que el
director vea lo mismo que imprime el admin:

- Las materias son las de `leer_materias_del_estudiante` en
  `boletin_repository`: la asignacion academica de cada clase activa, sin la
  materia de asistencia por jornada ni las materias inactivas.
- El puesto es el de `leer_puesto_en_el_curso` sin año: el `AVG` de las
  definitivas **guardadas** del periodo y `ROW_NUMBER()`, sin puestos
  repetidos (desempate: menos inasistencias del periodo, luego apellido y
  nombre).
- La definitiva de cada materia es la guardada, o el promedio de la planilla si
  no hay o es 0 (el `COALESCE(NULLIF(bc.definitiva, 0), ...)` del boletin); la
  eleccion la hace el controlador.
- Las inasistencias son las de `contar_inasistencias_por_periodo` en
  `estudiantes_repository` sin año.
"""

from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL


_ESTUDIANTE_ACTIVO = "COALESCE(LOWER(e.estado), 'activo') = 'activo'"


def leer_cursos_dirigidos(cursor, profesor_id):
    """Cursos activos del año activo que dirige el profesor."""
    cursor.execute(f'''
            SELECT c.id, c.nombre, c.jornada, c.nivel
            FROM cursos c
            WHERE c.director_grupo_id = %s
              AND c.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
              AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
            ORDER BY c.nombre
        ''', (profesor_id,))
    return cursor.fetchall()


def leer_curso(cursor, curso_id):
    """El curso, si es del año activo. `None` si no: eso es el 404."""
    cursor.execute(f'''
            SELECT c.id, c.nombre, c.jornada, c.nivel
            FROM cursos c
            WHERE c.id = %s
              AND c.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
        ''', (curso_id,))
    return cursor.fetchone()


def leer_materias_del_curso(cursor, curso_id, periodo, nombre_materia_excluida):
    """Materias del curso, en el orden del boletin, y si alguna definitiva
    guardada del periodo es de caritas (preescolar).

    La asignacion academica agrupa clases del mismo profesor, curso y materia
    (`resolver_asignacion_academica_id_cursor`), asi que filtrar por curso
    antes de elegir la de cada grupo da la misma que en el boletin.
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
                  AND a.curso_id = %s
                ORDER BY COALESCE(a.asignacion_academica_id, a.id), COALESCE(a.orden_boletin, 100), a.id
            )
            SELECT
                asig.id AS asignacion_id,
                m.nombre AS materia,
                p.nombre AS profesor_nombre,
                p.apellido AS profesor_apellido,
                asig.orden_boletin,
                EXISTS (
                    SELECT 1
                    FROM boletin_cabecera bc
                    JOIN boletin_detalles bd ON bd.boletin_id = bc.id
                    WHERE bc.asignacion_id = asig.id
                      AND bc.periodo = %s
                      AND bd.tipo_evaluacion = 'desarrollo'
                ) AS tiene_desarrollo
            FROM asignaciones_academicas asig
            JOIN materias m ON m.id = asig.materia_id
            JOIN profesor p ON p.id = asig.profesor_id
            WHERE m.nombre <> %s
              AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
            ORDER BY asig.orden_boletin, m.nombre
        ''', (curso_id, periodo, nombre_materia_excluida))
    return cursor.fetchall()


def leer_estudiantes_con_puesto(cursor, curso_id, periodo):
    """Estudiantes activos del curso con su promedio y su puesto del periodo.

    `promedios` y `ranked` son los de `leer_puesto_en_el_curso` sin año: entran
    todos los del curso con algo guardado, y el total de rankeados es el mismo
    "de N" del boletin. Quien no tiene nada guardado sale con puesto `NULL`, al
    final y por apellido.

    El puesto no se repite, con el mismo desempate que el boletin (2026-11-23):
    menos inasistencias del periodo -las de la columna de esta pantalla,
    `leer_inasistencias_del_curso`- y luego apellido y nombre; el `id` solo
    separa a dos con el mismo nombre completo.
    """
    cursor.execute(f'''
            WITH promedios AS (
                SELECT
                    bc.estudiante_id,
                    AVG(bc.definitiva) AS promedio
                FROM boletin_cabecera bc
                JOIN estudiantes e ON e.id = bc.estudiante_id
                JOIN asignaciones a ON a.id = bc.asignacion_id
                JOIN cursos c ON c.id = a.curso_id
                WHERE e.curso_id = %s
                  AND c.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
                  AND bc.periodo = %s
                  AND bc.definitiva IS NOT NULL
                GROUP BY bc.estudiante_id
            ),
            inasistencias AS (
                SELECT asi.estudiante_id, COUNT(*) AS ausencias
                FROM asistencia asi
                WHERE asi.estudiante_id IN (SELECT estudiante_id FROM promedios)
                  AND asi.estado ILIKE 'ausente'
                  AND COALESCE(asi.periodo, 1) = %s
                  AND (asi.asignacion_id IS NULL OR asi.asignacion_id IN (
                      SELECT a.id FROM asignaciones a
                      JOIN cursos c ON c.id = a.curso_id
                      WHERE c.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
                  ))
                GROUP BY asi.estudiante_id
            ),
            ranked AS (
                SELECT
                    p.estudiante_id,
                    p.promedio,
                    ROW_NUMBER() OVER (
                        ORDER BY p.promedio DESC,
                                 COALESCE(i.ausencias, 0),
                                 e.apellido, e.nombre, p.estudiante_id
                    ) AS puesto
                FROM promedios p
                JOIN estudiantes e ON e.id = p.estudiante_id
                LEFT JOIN inasistencias i ON i.estudiante_id = p.estudiante_id
            )
            SELECT
                e.id AS estudiante_id,
                e.nombre,
                e.apellido,
                r.promedio,
                r.puesto,
                (SELECT COUNT(*) FROM promedios) AS total_rankeados
            FROM estudiantes e
            LEFT JOIN ranked r ON r.estudiante_id = e.id
            WHERE e.curso_id = %s
              AND {_ESTUDIANTE_ACTIVO}
            ORDER BY r.puesto NULLS LAST, e.apellido, e.nombre
        ''', (curso_id, periodo, periodo, curso_id))
    return cursor.fetchall()


def leer_definitivas_del_curso(cursor, periodo, asignacion_ids):
    """Por estudiante y materia: la definitiva guardada (y si hay boletin
    guardado) y el promedio numerico de la planilla del periodo.

    El promedio de la planilla es el `nd_prom` de `leer_materias_del_estudiante`.
    Una fila por pareja con algo guardado o algo en la planilla.
    """
    cursor.execute('''
            WITH guardadas AS (
                SELECT bc.estudiante_id, bc.asignacion_id, bc.definitiva
                FROM boletin_cabecera bc
                WHERE bc.asignacion_id = ANY(%s)
                  AND bc.periodo = %s
            ),
            planilla AS (
                SELECT nd.estudiante_id, nd.asignacion_id, AVG(nd.nota) AS promedio
                FROM notas_detalle nd
                WHERE nd.asignacion_id = ANY(%s)
                  AND nd.periodo = %s
                  AND COALESCE(nd.tipo_evaluacion, 'numerica') <> 'desarrollo'
                  AND nd.nota > 0
                GROUP BY nd.estudiante_id, nd.asignacion_id
            )
            SELECT
                COALESCE(g.estudiante_id, p.estudiante_id) AS estudiante_id,
                COALESCE(g.asignacion_id, p.asignacion_id) AS asignacion_id,
                g.definitiva AS definitiva_guardada,
                (g.estudiante_id IS NOT NULL) AS guardada,
                p.promedio AS promedio_planilla
            FROM guardadas g
            FULL JOIN planilla p
              ON p.estudiante_id = g.estudiante_id
             AND p.asignacion_id = g.asignacion_id
        ''', (list(asignacion_ids), periodo, list(asignacion_ids), periodo))
    return cursor.fetchall()


def leer_inasistencias_del_curso(cursor, curso_id, periodo):
    """Ausencias del periodo y del año de cada estudiante activo del curso.

    La misma cuenta que `contar_inasistencias_por_periodo` sin año: todas las
    clases del año activo, mas las filas sin clase; un periodo vacio cuenta
    como el 1. Solo salen quienes tienen alguna.
    """
    cursor.execute(f'''
            SELECT
                asi.estudiante_id,
                count(*) FILTER (WHERE COALESCE(asi.periodo, 1) = %s) AS del_periodo,
                count(*) AS del_anio
            FROM asistencia asi
            JOIN estudiantes e ON e.id = asi.estudiante_id
            WHERE e.curso_id = %s
              AND {_ESTUDIANTE_ACTIVO}
              AND asi.estado ILIKE 'ausente'
              AND (asi.asignacion_id IS NULL OR asi.asignacion_id IN (
                  SELECT a.id FROM asignaciones a
                  JOIN cursos c ON c.id = a.curso_id
                  WHERE c.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
              ))
            GROUP BY asi.estudiante_id
        ''', (periodo, curso_id))
    return cursor.fetchall()


# --------------------------------------------------------------------------
# Observacion general del boletin (paso 3). Tabla
# `boletin_observacion_general`: una por estudiante, año y periodo.
# --------------------------------------------------------------------------

def leer_observaciones_del_curso(cursor, curso_id, periodo):
    """Observaciones generales del periodo de los estudiantes activos del
    curso, en el año activo. Solo salen quienes tienen una."""
    cursor.execute(f'''
            SELECT og.estudiante_id, og.texto, og.actualizado_en
            FROM boletin_observacion_general og
            JOIN estudiantes e ON e.id = og.estudiante_id
            WHERE e.curso_id = %s
              AND {_ESTUDIANTE_ACTIVO}
              AND og.periodo = %s
              AND og.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
        ''', (curso_id, periodo))
    return cursor.fetchall()


def estudiante_activo_en_curso(cursor, estudiante_id, curso_id):
    """`True` si el estudiante esta activo en ese curso y el curso es del año
    activo. Es lo que impide escribir la observacion de alguien de otro
    curso, aunque quien escribe dirija el suyo."""
    cursor.execute(f'''
            SELECT 1
            FROM estudiantes e
            JOIN cursos c ON c.id = e.curso_id
            WHERE e.id = %s
              AND e.curso_id = %s
              AND {_ESTUDIANTE_ACTIVO}
              AND c.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
        ''', (estudiante_id, curso_id))
    return cursor.fetchone() is not None


def guardar_observacion_general(cursor, estudiante_id, periodo, texto, rol, usuario_id):
    """Crea o reemplaza la observacion del estudiante en el periodo del año
    activo. Devuelve el texto y cuando quedo guardado."""
    cursor.execute(f'''
            INSERT INTO boletin_observacion_general (
                estudiante_id, anio_lectivo_id, periodo, texto,
                actualizado_por_rol, actualizado_por_id
            )
            VALUES (%s, {ANIO_ACTIVO_ID_SQL}, %s, %s, %s, %s)
            ON CONFLICT (estudiante_id, anio_lectivo_id, periodo)
            DO UPDATE SET
                texto = EXCLUDED.texto,
                actualizado_en = CURRENT_TIMESTAMP,
                actualizado_por_rol = EXCLUDED.actualizado_por_rol,
                actualizado_por_id = EXCLUDED.actualizado_por_id
            RETURNING texto, actualizado_en
        ''', (estudiante_id, periodo, texto, rol, usuario_id))
    return cursor.fetchone()


def borrar_observacion_general(cursor, estudiante_id, periodo):
    """Borra la observacion del estudiante en el periodo del año activo (un
    texto vacio no se guarda)."""
    cursor.execute(f'''
            DELETE FROM boletin_observacion_general
            WHERE estudiante_id = %s
              AND periodo = %s
              AND anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
        ''', (estudiante_id, periodo))


def leer_observacion_general(cursor, estudiante_id, periodo, anio_lectivo_id=None):
    """La observacion de un estudiante para el boletin del admin. Sin
    `anio_lectivo_id`, la del año activo, como el resto de ese boletin."""
    anio_sql, params_anio = (
        (ANIO_ACTIVO_ID_SQL, ()) if anio_lectivo_id is None else ("%s", (anio_lectivo_id,))
    )
    cursor.execute(f'''
            SELECT texto
            FROM boletin_observacion_general
            WHERE estudiante_id = %s
              AND periodo = %s
              AND anio_lectivo_id = {anio_sql}
        ''', (estudiante_id, periodo, *params_anio))
    return cursor.fetchone()
