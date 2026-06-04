ALTER TABLE materias
    ADD COLUMN IF NOT EXISTS estado VARCHAR(30);

UPDATE materias
SET estado = 'activo'
WHERE estado IS NULL OR TRIM(estado) = '';

CREATE INDEX IF NOT EXISTS idx_materias_estado
ON materias (estado);
