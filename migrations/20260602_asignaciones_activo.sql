ALTER TABLE asignaciones
    ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE asignaciones
SET activo = TRUE
WHERE activo IS NULL;

CREATE INDEX IF NOT EXISTS idx_asignaciones_activo
    ON asignaciones(activo);

CREATE INDEX IF NOT EXISTS idx_asignaciones_profesor_dia_activo
    ON asignaciones(profesor_id, dia, activo);

CREATE INDEX IF NOT EXISTS idx_asignaciones_curso_dia_activo
    ON asignaciones(curso_id, dia, activo);
