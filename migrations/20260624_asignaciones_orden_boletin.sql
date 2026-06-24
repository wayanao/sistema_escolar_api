-- Permite configurar el orden de materias en boletines por curso.

ALTER TABLE asignaciones
ADD COLUMN IF NOT EXISTS orden_boletin INTEGER NOT NULL DEFAULT 100;

UPDATE asignaciones
SET orden_boletin = 100
WHERE orden_boletin IS NULL;

CREATE INDEX IF NOT EXISTS idx_asignaciones_curso_orden_boletin
ON asignaciones (curso_id, orden_boletin, materia_id)
WHERE activo = TRUE;
