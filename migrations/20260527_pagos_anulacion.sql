-- Anulacion auditada de pagos.
-- Los pagos no se eliminan: se marcan como Anulado y quedan visibles como huella.

ALTER TABLE pagos
    ADD COLUMN IF NOT EXISTS estado VARCHAR(50) NOT NULL DEFAULT 'Pagado',
    ADD COLUMN IF NOT EXISTS motivo_anulacion TEXT,
    ADD COLUMN IF NOT EXISTS fecha_anulacion TIMESTAMP,
    ADD COLUMN IF NOT EXISTS anulado_por INTEGER;

UPDATE pagos
SET estado = 'Pagado'
WHERE estado IS NULL OR TRIM(estado) = '';

CREATE INDEX IF NOT EXISTS idx_pagos_estado ON pagos(estado);
