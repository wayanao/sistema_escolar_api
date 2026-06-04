ALTER TABLE inventario
    ADD COLUMN IF NOT EXISTS estado VARCHAR(30);

UPDATE inventario
SET estado = 'activo'
WHERE estado IS NULL OR TRIM(estado) = '';

CREATE INDEX IF NOT EXISTS idx_inventario_estado
ON inventario (estado);
