ALTER TABLE profesor
    ADD COLUMN IF NOT EXISTS estado VARCHAR(30);

UPDATE profesor
SET estado = 'activo'
WHERE estado IS NULL OR TRIM(estado) = '';

CREATE INDEX IF NOT EXISTS idx_profesor_estado
ON profesor (estado);
