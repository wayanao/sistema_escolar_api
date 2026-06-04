ALTER TABLE egresos
    ADD COLUMN IF NOT EXISTS origen VARCHAR(30);

UPDATE egresos
SET origen = 'nomina'
WHERE origen IS NULL
  AND LOWER(TRIM(COALESCE(categoria, ''))) = 'pago nomina';

UPDATE egresos
SET origen = 'manual'
WHERE origen IS NULL OR TRIM(origen) = '';

CREATE INDEX IF NOT EXISTS idx_egresos_origen
ON egresos (origen);
