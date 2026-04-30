-- Ejecutar en cada schema tenant.
ALTER TABLE pagos
    ALTER COLUMN tipo_pago TYPE VARCHAR(100);
