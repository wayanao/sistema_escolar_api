-- Ejecutar en cada schema tenant.
ALTER TABLE plan_de_clases
    ADD COLUMN IF NOT EXISTS periodo INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS clase TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS actividad_casa TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

UPDATE plan_de_clases SET periodo = 1 WHERE periodo IS NULL;
UPDATE plan_de_clases SET clase = '' WHERE clase IS NULL;
UPDATE plan_de_clases SET actividad_casa = '' WHERE actividad_casa IS NULL;

CREATE INDEX IF NOT EXISTS idx_plan_de_clases_asignacion_fecha
    ON plan_de_clases(asignacion_id, fecha);

CREATE INDEX IF NOT EXISTS idx_plan_de_clases_fecha
    ON plan_de_clases(fecha);
