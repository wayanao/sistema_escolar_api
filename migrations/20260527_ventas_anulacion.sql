-- Anulacion auditada de ventas de inventario.
-- Las ventas no se eliminan: se marcan como Anulada y devuelven stock.

ALTER TABLE ventas
    ADD COLUMN IF NOT EXISTS motivo_anulacion TEXT,
    ADD COLUMN IF NOT EXISTS fecha_anulacion TIMESTAMP,
    ADD COLUMN IF NOT EXISTS anulado_por INTEGER;

CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas(estado);
