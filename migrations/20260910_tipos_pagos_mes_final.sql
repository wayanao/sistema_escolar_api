-- =====================================================================
-- Migracion: mes final de cobros recurrentes
-- Fecha: 2026-09-10
--
-- Limita el ultimo mes que genera una mensualidad dentro del anio escolar.
-- Diciembre conserva el comportamiento historico de los conceptos existentes.
-- Se aplica por tenant con apply_migration.py.
-- =====================================================================

ALTER TABLE tipos_de_pagos
    ADD COLUMN IF NOT EXISTS mes_final SMALLINT;

UPDATE tipos_de_pagos
SET mes_final = 12
WHERE mes_final IS NULL;

ALTER TABLE tipos_de_pagos
    ALTER COLUMN mes_final SET DEFAULT 12,
    ALTER COLUMN mes_final SET NOT NULL;

ALTER TABLE tipos_de_pagos DROP CONSTRAINT IF EXISTS chk_mes_final;
ALTER TABLE tipos_de_pagos
    ADD CONSTRAINT chk_mes_final
    CHECK (mes_final BETWEEN 1 AND 12);

ALTER TABLE tipos_de_pagos DROP CONSTRAINT IF EXISTS chk_rango_meses_recurrencia;
ALTER TABLE tipos_de_pagos
    ADD CONSTRAINT chk_rango_meses_recurrencia
    CHECK (
        tipo_cobro <> 'mensual'
        OR mes_inicial IS NULL
        OR mes_final >= mes_inicial
    );
