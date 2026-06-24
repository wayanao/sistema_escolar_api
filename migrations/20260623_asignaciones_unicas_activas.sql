-- Corrige asignaciones academicas duplicadas y evita que se repitan.
-- Mantiene activa la asignacion con mas historial; si ninguna tiene historial,
-- conserva la mas reciente.

WITH historial AS (
    SELECT
        a.id AS asignacion_id,
        (
            (SELECT COUNT(*) FROM notas_detalle nd WHERE nd.asignacion_id = a.id) +
            (SELECT COUNT(*) FROM boletin_cabecera bc WHERE bc.asignacion_id = a.id) +
            (SELECT COUNT(*) FROM asistencia asi WHERE asi.asignacion_id = a.id) +
            (SELECT COUNT(*) FROM observaciones o WHERE o.asignacion_id = a.id) +
            (SELECT COUNT(*) FROM plan_de_clases pc WHERE pc.asignacion_id = a.id) +
            (SELECT COUNT(*) FROM planeador_anual pa WHERE pa.asignacion_id = a.id)
        ) AS total_historial
    FROM asignaciones a
),
ranked AS (
    SELECT
        a.id,
        ROW_NUMBER() OVER (
            PARTITION BY a.profesor_id, a.curso_id, a.materia_id
            ORDER BY h.total_historial DESC, a.id DESC
        ) AS posicion
    FROM asignaciones a
    JOIN historial h ON h.asignacion_id = a.id
    WHERE a.activo = TRUE
)
UPDATE asignaciones a
SET activo = FALSE
FROM ranked r
WHERE a.id = r.id
  AND r.posicion > 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_asignaciones_profesor_curso_materia_activa_unico
ON asignaciones (profesor_id, curso_id, materia_id)
WHERE activo = TRUE;
