-- Vincula pagos con ventas de inventario para permitir anulacion segura.

ALTER TABLE pagos
    ADD COLUMN IF NOT EXISTS venta_id INTEGER REFERENCES ventas(id);

CREATE INDEX IF NOT EXISTS idx_pagos_venta_id ON pagos(venta_id);
