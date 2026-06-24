-- Ajusta asignaciones para separar horario de historial academico.
-- Regla:
-- 1) Un curso + materia tiene un solo profesor responsable activo.
-- 2) Ese profesor puede tener varios horarios activos para la misma materia.
-- 3) Todos esos horarios apuntan a una sola asignacion academica para notas e historial.

ALTER TABLE asignaciones
ADD COLUMN IF NOT EXISTS asignacion_academica_id INTEGER REFERENCES asignaciones(id);

DROP INDEX IF EXISTS idx_asignaciones_profesor_curso_materia_activa_unico;

-- Reactiva unicamente los horarios que quedaron inactivos por la migracion
-- anterior y que no tienen historial propio. Se acota por schema e id.
UPDATE asignaciones
SET activo = TRUE
WHERE current_schema() = 'tenant_colegio_1'
  AND id IN (122, 123, 124)
  AND NOT EXISTS (SELECT 1 FROM notas_detalle nd WHERE nd.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM boletin_cabecera bc WHERE bc.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM asistencia asi WHERE asi.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM observaciones o WHERE o.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM plan_de_clases pc WHERE pc.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM planeador_anual pa WHERE pa.asignacion_id = asignaciones.id);

UPDATE asignaciones
SET activo = TRUE
WHERE current_schema() = 'tenant_2005'
  AND id IN (129, 133, 135, 136, 137)
  AND NOT EXISTS (SELECT 1 FROM notas_detalle nd WHERE nd.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM boletin_cabecera bc WHERE bc.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM asistencia asi WHERE asi.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM observaciones o WHERE o.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM plan_de_clases pc WHERE pc.asignacion_id = asignaciones.id)
  AND NOT EXISTS (SELECT 1 FROM planeador_anual pa WHERE pa.asignacion_id = asignaciones.id);

WITH historial AS (
    SELECT
        a.id,
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
canonica AS (
    SELECT
        a.id,
        FIRST_VALUE(a.id) OVER (
            PARTITION BY a.profesor_id, a.curso_id, a.materia_id
            ORDER BY
                CASE WHEN a.activo = TRUE THEN 0 ELSE 1 END,
                h.total_historial DESC,
                a.id ASC
        ) AS asignacion_academica_id
    FROM asignaciones a
    JOIN historial h ON h.id = a.id
)
UPDATE asignaciones a
SET asignacion_academica_id = c.asignacion_academica_id
FROM canonica c
WHERE a.id = c.id;

UPDATE asignaciones
SET asignacion_academica_id = id
WHERE asignacion_academica_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_asignaciones_academica_id
ON asignaciones (asignacion_academica_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_asignaciones_horario_activo_unico
ON asignaciones (profesor_id, curso_id, materia_id, dia, hora_inicio, hora_fin)
WHERE activo = TRUE;

CREATE OR REPLACE FUNCTION validar_profesor_responsable_materia_curso()
RETURNS trigger AS $$
BEGIN
    IF NEW.activo = TRUE AND EXISTS (
        SELECT 1
        FROM asignaciones a
        WHERE a.activo = TRUE
          AND a.curso_id = NEW.curso_id
          AND a.materia_id = NEW.materia_id
          AND a.profesor_id <> NEW.profesor_id
          AND a.id <> COALESCE(NEW.id, -1)
    ) THEN
        RAISE EXCEPTION 'Esta materia ya tiene otro profesor asignado en este curso.'
            USING ERRCODE = '23505';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_profesor_responsable_materia_curso ON asignaciones;

CREATE TRIGGER trg_profesor_responsable_materia_curso
BEFORE INSERT OR UPDATE OF profesor_id, curso_id, materia_id, activo
ON asignaciones
FOR EACH ROW
EXECUTE FUNCTION validar_profesor_responsable_materia_curso();
