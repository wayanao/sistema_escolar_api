-- Repara punteros academicos inconsistentes sin borrar datos.
-- Solo actualiza asignacion_academica_id cuando apunta a otra combinacion
-- de profesor, curso o materia. No toca notas, asistencia, planes ni estudiantes.

WITH base_por_grupo AS (
    SELECT
        profesor_id,
        curso_id,
        materia_id,
        MIN(id) AS asignacion_academica_id
    FROM asignaciones
    WHERE activo = TRUE
    GROUP BY profesor_id, curso_id, materia_id
), inconsistentes AS (
    SELECT
        a.id,
        base_por_grupo.asignacion_academica_id
    FROM asignaciones a
    JOIN asignaciones apuntada ON apuntada.id = a.asignacion_academica_id
    JOIN base_por_grupo
      ON base_por_grupo.profesor_id = a.profesor_id
     AND base_por_grupo.curso_id = a.curso_id
     AND base_por_grupo.materia_id = a.materia_id
    WHERE a.activo = TRUE
      AND a.asignacion_academica_id IS NOT NULL
      AND (
          apuntada.profesor_id <> a.profesor_id
          OR apuntada.curso_id <> a.curso_id
          OR apuntada.materia_id <> a.materia_id
      )
)
UPDATE asignaciones a
SET asignacion_academica_id = inconsistentes.asignacion_academica_id
FROM inconsistentes
WHERE a.id = inconsistentes.id;
