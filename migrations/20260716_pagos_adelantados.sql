-- =====================================================================
-- Migracion: aplicaciones mensuales para pagos adelantados
-- Fecha: 2026-07-16
--
-- Mantiene `pagos` como libro de caja y registra por separado los meses
-- futuros cubiertos. Se aplica en cada schema tenant con apply_migration.py.
-- =====================================================================

CREATE TABLE IF NOT EXISTS pagos_aplicaciones (
    id BIGSERIAL PRIMARY KEY,
    pago_id INTEGER NOT NULL REFERENCES pagos(id),
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id),
    tipo_pago_id INTEGER NOT NULL REFERENCES tipos_de_pagos(id),
    periodo DATE NOT NULL,
    monto NUMERIC(12, 2) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_pagos_aplicaciones_periodo_inicio_mes
        CHECK (EXTRACT(DAY FROM periodo) = 1),
    CONSTRAINT chk_pagos_aplicaciones_monto_positivo
        CHECK (monto > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pagos_aplicaciones_activas
    ON pagos_aplicaciones (estudiante_id, tipo_pago_id, periodo)
    WHERE activo = TRUE;

CREATE INDEX IF NOT EXISTS idx_pagos_aplicaciones_pago
    ON pagos_aplicaciones (pago_id);

CREATE INDEX IF NOT EXISTS idx_pagos_aplicaciones_estudiante_periodo
    ON pagos_aplicaciones (estudiante_id, periodo);
