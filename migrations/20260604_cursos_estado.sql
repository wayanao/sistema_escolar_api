ALTER TABLE cursos
    ADD COLUMN IF NOT EXISTS estado VARCHAR(30);

UPDATE cursos
SET estado = 'activo'
WHERE estado IS NULL OR TRIM(estado) = '';

CREATE INDEX IF NOT EXISTS idx_cursos_estado
ON cursos (estado);
